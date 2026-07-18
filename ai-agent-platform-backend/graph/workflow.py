"""LangGraph core reasoning pipeline (no LLM calls).

Wires the agent-core reasoning steps into a single linear LangGraph over the
shared :class:`AgentState` from Step 2:

    Input -> Intent -> Emotion -> Agent Loader -> Memory Retrieval
          -> Context Builder -> Prompt Builder

Each node is a pure-ish function that reads the state and returns a partial
update. This step produces a fully-built ``prompt`` but deliberately stops
short of calling any LLM — generation belongs to the orchestrator (Step 7),
invoked in a later step.

Nodes integrate with earlier layers (agent loader, memory service) but never
modify them, and every external call is wrapped so a failure degrades
gracefully instead of crashing the graph.
"""

import logging
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from graph.safety_node import safety_node
from graph.state import (
    MAX_REFLECT_ITERS,
    MAX_RETRIEVE_ITERS,
    MAX_TOOL_ITERS,
    AgentState,
    append_trace,
)
from llm.llm_router import route_llm, route_tools
from llm.reflection import REVISE, reflect_on_response
from tools.registry import default_registry
from memory.memory_service import get_relevant_memories
from memory.query_planner import (
    best_relevance,
    grade_memories,
    plan_query,
    reformulate_query,
)
from memory.writeback.writeback_engine import process_writeback
from safety.engine import SafetyEngine
from services.agent_loader import AgentLoaderError, AgentLoaderService
from services.classifiers import classify_intent, detect_emotion, select_route
from services.classifiers.route_selector import (
    ROUTE_CRISIS,
    ROUTE_DIRECT,
    ROUTE_RETRIEVE,
    ROUTE_TOOL,
)

logger = logging.getLogger("agent_core")

# Safety ceiling on graph steps. Three bounded loops (retrieval + tool ReAct +
# reflection) can compound, so this sits comfortably above their worst-case
# combined length; the real bounds are the ``MAX_*_ITERS`` counters.
RECURSION_LIMIT = 80


# ----------------------------------------------------------------------
# NODE 1 — Input: receive + validate the incoming message
# ----------------------------------------------------------------------
def input_node(state: AgentState) -> Dict[str, Any]:
    safety_flags = dict(state.get("safety_flags") or {})
    message = (state.get("message") or "").strip()

    missing = [
        field for field in ("user_id", "agent_id", "session_id") if not state.get(field)
    ]
    if missing:
        safety_flags["invalid_input"] = True
        safety_flags["missing_fields"] = missing
        logger.warning("Input node: missing required fields: %s", missing)
    if not message:
        safety_flags["empty_message"] = True
        logger.warning("Input node: empty message")

    blocked = bool(missing) or not message
    details = {"missing": missing} if missing else {}
    return {
        "message": message,
        "safety_flags": safety_flags,
        "trace": append_trace(
            state, "input", "blocked" if blocked else "accepted", **details
        ),
    }


# ----------------------------------------------------------------------
# NODE 2 — Intent classification
# ----------------------------------------------------------------------
def intent_node(state: AgentState) -> Dict[str, Any]:
    intent = classify_intent(state.get("message", ""))
    safety_flags = dict(state.get("safety_flags") or {})
    if intent == "crisis":
        safety_flags["crisis"] = True
    logger.debug("Intent node -> %s", intent)
    return {
        "intent": intent,
        "safety_flags": safety_flags,
        "trace": append_trace(state, "intent", intent or "unknown"),
    }


# ----------------------------------------------------------------------
# NODE 3 — Emotion detection
# ----------------------------------------------------------------------
def emotion_node(state: AgentState) -> Dict[str, Any]:
    emotion = detect_emotion(state.get("message", ""))
    logger.debug("Emotion node -> %s", emotion)
    return {"emotion": emotion}


# ----------------------------------------------------------------------
# NODE 3.5 — Router: pick the pipeline path (agentic conditional control)
# ----------------------------------------------------------------------
def router_node(state: AgentState) -> Dict[str, Any]:
    """Decide the route for this turn and record it on ``state['route']``.

    Reuses the deterministic intent classifier (already applied by the intent
    node) plus a tool-need heuristic. The route drives the conditional edges:
    ``crisis`` takes the LLM-free fast-path, ``direct`` skips retrieval,
    ``retrieve`` / ``tool`` enter the memory pipeline.
    """
    route = select_route(state.get("intent") or "", state.get("message", ""))
    logger.debug("Router node -> %s", route)
    return {"route": route, "trace": append_trace(state, "router", route)}


def route_from_router(state: AgentState) -> str:
    """Conditional-edge selector: crisis forks to the fast-path, else continue."""
    return ROUTE_CRISIS if state.get("route") == ROUTE_CRISIS else "proceed"


def route_after_agent_loader(state: AgentState) -> str:
    """Conditional-edge selector: ``direct`` skips retrieval, others retrieve."""
    return "direct" if state.get("route") == ROUTE_DIRECT else "retrieve"


def route_after_safety(state: AgentState) -> str:
    """Conditional-edge selector: crisis ends after safety, else finalize."""
    return "end" if state.get("route") == ROUTE_CRISIS else "continue"


# ----------------------------------------------------------------------
# NODE 3.6 — Crisis response: deterministic, LLM-free support message
# ----------------------------------------------------------------------
def crisis_response_node(state: AgentState) -> Dict[str, Any]:
    """Emit the deterministic crisis support message — no retrieval, no LLM.

    The safety engine owns the exact wording so the crisis text stays in one
    place. The downstream safety node re-affirms it (idempotent).
    """
    safety_flags = dict(state.get("safety_flags") or {})
    safety_flags["crisis"] = True
    response = SafetyEngine().build_crisis_response()
    logger.warning("Crisis fast-path: returning deterministic support message (no LLM).")
    return {
        "response": response,
        "safety_flags": safety_flags,
        "trace": append_trace(state, "crisis_response", "support_message"),
    }


# ----------------------------------------------------------------------
# NODE 4 — Agent loader (integrates Step 3, never modifies it)
# ----------------------------------------------------------------------
def agent_loader_node(state: AgentState) -> Dict[str, Any]:
    safety_flags = dict(state.get("safety_flags") or {})
    try:
        profile = AgentLoaderService().get_agent(state["agent_id"])
        return {
            "agent_config": profile.to_dict(),
            "trace": append_trace(state, "agent_loader", "loaded"),
        }
    except AgentLoaderError as exc:
        logger.warning("Agent loader node: could not load agent: %s", exc)
        safety_flags["agent_unavailable"] = True
        return {
            "agent_config": {},
            "safety_flags": safety_flags,
            "trace": append_trace(state, "agent_loader", "unavailable", error=str(exc)),
        }
    except Exception as exc:  # noqa: BLE001 — never crash the graph
        logger.error("Agent loader node: unexpected error: %s", exc)
        safety_flags["agent_unavailable"] = True
        return {
            "agent_config": {},
            "safety_flags": safety_flags,
            "trace": append_trace(state, "agent_loader", "unavailable", error=str(exc)),
        }


# ----------------------------------------------------------------------
# NODE 5a — Plan query: rewrite the user message into a search query
# ----------------------------------------------------------------------
def plan_query_node(state: AgentState) -> Dict[str, Any]:
    """Seed the retrieval loop with a focused search query."""
    query = plan_query(state.get("message", ""))
    logger.debug("Plan-query node -> %r", query)
    return {"search_query": query, "trace": append_trace(state, "plan_query", "planned")}


# ----------------------------------------------------------------------
# NODE 5b — Retrieve: hybrid memory search for the current search_query
# ----------------------------------------------------------------------
def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """Run one retrieval pass and record the flattened candidate pool.

    Uses ``search_query`` (set by plan/reformulate; falls back to the raw
    message), increments ``retrieve_iters``, and aggregates every hit into
    ``retrieved`` for the grader. Populates the per-collection memory fields the
    context builder consumes, so the last (best) pass grounds the response.
    """
    context = dict(state.get("context") or {})
    query = state.get("search_query") or state.get("message", "")
    iters = int(state.get("retrieve_iters") or 0) + 1

    try:
        memories = get_relevant_memories(
            query=query,
            user_id=state["user_id"],
            agent_id=state["agent_id"],
            top_k=5,
        )
    except Exception as exc:  # noqa: BLE001 — memory must never crash reasoning
        logger.warning("Retrieve node: retrieval failed: %s", exc)
        memories = {}

    retrieved: List[Dict[str, Any]] = []
    for hits in memories.values():
        retrieved.extend(hits)

    context["emotional_memory"] = memories.get("emotional_memory", [])
    return {
        "user_memory": memories.get("user_memory", []),
        "conversation_memory": memories.get("conversation_memory", []),
        "agent_memory": memories.get("agent_behavior_memory", []),
        "retrieved": retrieved,
        "retrieve_iters": iters,
        "context": context,
        "trace": append_trace(state, "retrieve", f"pass_{iters}", hits=len(retrieved)),
    }


# ----------------------------------------------------------------------
# NODE 5c — Grade: are the retrieved memories good enough to ground on?
# ----------------------------------------------------------------------
def grade_node(state: AgentState) -> Dict[str, Any]:
    """Score the latest retrieval pass as sufficient / insufficient."""
    retrieved = state.get("retrieved") or []
    grade = grade_memories(retrieved)
    best = round(best_relevance(retrieved), 4)
    logger.debug("Grade node -> %s (best_relevance=%.4f)", grade, best)
    return {
        "relevance_grade": grade,
        "trace": append_trace(state, "grade", grade, best_relevance=best),
    }


# ----------------------------------------------------------------------
# NODE 5d — Reformulate: produce an improved query, then loop to retrieve
# ----------------------------------------------------------------------
def reformulate_node(state: AgentState) -> Dict[str, Any]:
    """Improve the search query for another retrieval pass."""
    iteration = int(state.get("retrieve_iters") or 0)
    query = reformulate_query(
        state.get("message", ""),
        iteration=iteration,
        emotion=state.get("emotion"),
        intent=state.get("intent"),
    )
    logger.debug("Reformulate node -> %r (iteration=%d)", query, iteration)
    return {
        "search_query": query,
        "trace": append_trace(state, "reformulate", "requery", iteration=iteration),
    }


def route_after_grade(state: AgentState) -> str:
    """Conditional-edge selector for the retrieval loop.

    Loop back to ``reformulate`` while the grade is insufficient AND the loop
    budget (``MAX_RETRIEVE_ITERS``) is not exhausted; otherwise proceed to
    generation best-effort.
    """
    insufficient = state.get("relevance_grade") == "insufficient"
    has_budget = int(state.get("retrieve_iters") or 0) < MAX_RETRIEVE_ITERS
    return "reformulate" if (insufficient and has_budget) else "generate"


# ----------------------------------------------------------------------
# NODE 6 — Context builder: merge everything the prompt needs
# ----------------------------------------------------------------------
def context_builder_node(state: AgentState) -> Dict[str, Any]:
    agent_config = state.get("agent_config") or {}
    context = dict(state.get("context") or {})
    context.update(
        {
            "agent_id": state.get("agent_id"),
            "display_name": agent_config.get("display_name"),
            "persona_prompt": agent_config.get("persona_prompt", ""),
            "behavior_rules": agent_config.get("behavior_rules", ""),
            "safety_rules": agent_config.get("safety_rules", {}),
            "intent": state.get("intent"),
            "emotion": state.get("emotion"),
            "message": state.get("message"),
            "user_memory": state.get("user_memory", []),
            "conversation_memory": state.get("conversation_memory", []),
            "agent_memory": state.get("agent_memory", []),
            # Reflection critique from a prior revise pass (None on first pass).
            "reflection": state.get("reflection"),
        }
    )
    logger.debug("Context builder node: context assembled")
    return {"context": context}


# ----------------------------------------------------------------------
# NODE 7 — Prompt builder: assemble the structured prompt (NO LLM call)
# ----------------------------------------------------------------------
def _format_memories(label: str, memories: List[Dict[str, Any]]) -> str:
    if not memories:
        return ""
    lines = [f"{label}:"]
    for item in memories:
        content = item.get("content")
        if content:
            lines.append(f"- {content}")
    return "\n".join(lines) if len(lines) > 1 else ""


def prompt_builder_node(state: AgentState) -> Dict[str, Any]:
    context = state.get("context") or {}

    persona = context.get("persona_prompt") or "You are a helpful AI companion."
    behavior = context.get("behavior_rules") or ""
    intent = context.get("intent") or "casual"
    emotion = context.get("emotion") or "neutral"
    message = context.get("message") or ""

    sections: List[str] = [f"[PERSONA]\n{persona}"]
    if behavior:
        sections.append(f"[BEHAVIOR RULES]\n{behavior}")

    user_mem = _format_memories("What you know about the user", context.get("user_memory", []))
    if user_mem:
        sections.append(f"[USER MEMORY]\n{user_mem}")

    convo_mem = _format_memories("Relevant past conversation", context.get("conversation_memory", []))
    if convo_mem:
        sections.append(f"[CONVERSATION MEMORY]\n{convo_mem}")

    emo_mem = _format_memories("Emotional history", context.get("emotional_memory", []))
    if emo_mem:
        sections.append(f"[EMOTIONAL MEMORY]\n{emo_mem}")

    sections.append(f"[UNDERSTANDING]\nDetected intent: {intent}\nDetected emotion: {emotion}")
    sections.append(f"[USER MESSAGE]\n{message}")

    # On a revision pass, a prior draft was judged weak — steer the retry.
    reflection = (context.get("reflection") or "").strip()
    if reflection:
        sections.append(
            "[REVISION NOTE]\nYour previous draft was rejected. Fix this and try "
            f"again: {reflection}"
        )

    sections.append("[TASK]\nRespond in character, honoring the persona, behavior rules, and the user's emotional state.")

    prompt = "\n\n".join(sections)
    logger.debug("Prompt builder node: prompt assembled (%d chars)", len(prompt))
    return {"prompt": prompt}


# ----------------------------------------------------------------------
# NODE 8 — LLM orchestrator (Step 7): the ONLY place a model is called
# ----------------------------------------------------------------------
def llm_node(state: AgentState) -> Dict[str, Any]:
    context = dict(state.get("context") or {})
    # Crisis turns ask for the highest-quality provider; otherwise default.
    routing = {
        "intent": context.get("intent"),
        "quality": "high" if context.get("intent") == "crisis" else None,
    }
    result = route_llm(state.get("prompt", ""), routing)
    context["llm_provider"] = result.get("provider")
    context["llm_ok"] = result.get("ok")
    logger.debug("LLM node: provider=%s ok=%s", result.get("provider"), result.get("ok"))
    return {"response": result.get("response", ""), "context": context}


def route_after_prompt(state: AgentState) -> str:
    """Conditional-edge selector: the ``tool`` route enters the ReAct loop."""
    return "tool" if state.get("route") == ROUTE_TOOL else "generate"


# ----------------------------------------------------------------------
# NODE 8t — Tool agent (ReAct): decide to call a tool or answer directly
# ----------------------------------------------------------------------
def _with_observations(text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Append accumulated tool observations to ``text`` (the ReAct scratchpad)."""
    if not tool_results:
        return text
    lines = ["", "[TOOL OBSERVATIONS]"]
    for item in tool_results:
        lines.append(f"- {item.get('name')}: {item.get('observation')}")
    return f"{text}\n" + "\n".join(lines)


def tool_agent_node(state: AgentState) -> Dict[str, Any]:
    """One ReAct step: ask a tool-capable model to use a tool or give a final answer.

    Rebuilds the prompt + accumulated observations each round (so a later
    revision pass starts fresh), then:

    * model requests tool(s) → store ``tool_calls`` for the executor;
    * model returns text → that is the final draft;
    * no tool-capable provider / budget exhausted → degrade to a plain
      generation grounded in the observations gathered so far.
    """
    prompt = state.get("prompt", "")
    tool_results = list(state.get("tool_results") or [])
    tool_iters = int(state.get("tool_iters") or 0)
    context = state.get("context") or {}

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": _with_observations(state.get("message", ""), tool_results)},
    ]

    result: Dict[str, Any] = {"ok": False}
    if tool_iters < MAX_TOOL_ITERS:
        result = route_tools(messages, default_registry.schemas(), context)

    if result.get("ok") and result.get("type") == "tool_calls":
        calls = result.get("tool_calls") or []
        names = [call.get("name") for call in calls]
        logger.debug("Tool agent: model requested tools %s", names)
        return {
            "tool_calls": calls,
            "trace": append_trace(state, "tool_agent", "use_tool", tools=names),
        }

    if result.get("ok") and result.get("type") == "text":
        return {
            "response": result.get("text", ""),
            "tool_calls": [],
            "trace": append_trace(state, "tool_agent", "final_answer"),
        }

    # Degrade / budget exhausted: produce a final reply with plain generation,
    # grounded in whatever observations were gathered.
    reason = "budget_exhausted" if tool_iters >= MAX_TOOL_ITERS else "no_tool_provider"
    final = route_llm(_with_observations(prompt, tool_results), {"intent": state.get("intent")})
    return {
        "response": final.get("response", ""),
        "tool_calls": [],
        "trace": append_trace(state, "tool_agent", "final_answer", degraded=reason),
    }


def route_after_tool_agent(state: AgentState) -> str:
    """Conditional-edge selector: pending tool calls execute, otherwise reflect."""
    return "execute" if state.get("tool_calls") else "done"


# ----------------------------------------------------------------------
# NODE 8x — Tool executor: run the requested tools, record observations
# ----------------------------------------------------------------------
def tool_executor_node(state: AgentState) -> Dict[str, Any]:
    """Execute pending ``tool_calls`` and append their observations, then loop."""
    tool_calls = state.get("tool_calls") or []
    results = list(state.get("tool_results") or [])
    exec_context = {
        **(state.get("context") or {}),
        "user_id": state.get("user_id", ""),
        "agent_id": state.get("agent_id", ""),
        "emotion": state.get("emotion"),
    }

    executed: List[str] = []
    for call in tool_calls:
        name = call.get("name", "")
        arguments = call.get("arguments") or {}
        outcome = default_registry.execute(name, arguments, exec_context)
        observation = outcome.to_observation()
        results.append(
            {
                "name": name,
                "arguments": arguments,
                "ok": outcome.ok,
                "observation": observation,
            }
        )
        executed.append(name)
        logger.debug("Tool executor: %s -> %s", name, observation)

    return {
        "tool_results": results,
        "tool_calls": [],
        "tool_iters": int(state.get("tool_iters") or 0) + 1,
        "trace": append_trace(state, "tool_executor", "observed", tools=executed),
    }


# ----------------------------------------------------------------------
# NODE 8.5 — Reflection: cheap-model critic over the draft (quality, not safety)
# ----------------------------------------------------------------------
def reflect_node(state: AgentState) -> Dict[str, Any]:
    """Judge the draft (grounded / in-persona / emotion-aware) → accept | revise.

    Best-effort quality gate that fails open: any critic failure accepts the
    draft. On ``revise`` it stores the critique so the next generation attempt
    can act on it, and increments ``reflect_iters`` to bound the loop.
    """
    context = state.get("context") or {}
    memories = list(state.get("retrieved") or []) or list(state.get("user_memory") or [])
    result = reflect_on_response(
        message=state.get("message", ""),
        draft=state.get("response", "") or "",
        memories=memories,
        persona=context.get("persona_prompt", ""),
        emotion=state.get("emotion"),
    )
    verdict = result.get("verdict", "accept")
    iters = int(state.get("reflect_iters") or 0) + 1

    update: Dict[str, Any] = {
        "reflect_verdict": verdict,
        "reflect_iters": iters,
        "trace": append_trace(state, "reflect", verdict, iteration=iters),
    }
    # Carry the critique forward only when revising, so the prompt builder can
    # inject it; clear it on accept so a stale note never leaks into the reply.
    update["reflection"] = result.get("critique", "") if verdict == REVISE else None
    return update


def route_after_reflect(state: AgentState) -> str:
    """Conditional-edge selector: revise (bounded) loops back, else go to safety."""
    revise = state.get("reflect_verdict") == REVISE
    has_budget = int(state.get("reflect_iters") or 0) < MAX_REFLECT_ITERS
    return "revise" if (revise and has_budget) else "accept"


# ----------------------------------------------------------------------
# NODE 9 — Safety engine (Step 8): post-LLM gatekeeper (graph.safety_node)
# Registered directly as `safety_node`; see edges below.
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# NODE 10 — Response finalizer: guarantee a non-empty, clean final reply
# ----------------------------------------------------------------------
def response_finalizer_node(state: AgentState) -> Dict[str, Any]:
    response = (state.get("response") or "").strip()
    if not response:
        response = "I'm here with you. Tell me a little more about what's on your mind."
    return {"response": response}


# ----------------------------------------------------------------------
# NODE 11 — Memory writeback (Step 9): learn from this exchange
# ----------------------------------------------------------------------
def writeback_node(state: AgentState) -> Dict[str, Any]:
    messages = [
        {"role": "user", "content": state.get("message", "")},
        {"role": "assistant", "content": state.get("response", "")},
    ]
    try:
        updates = process_writeback(
            user_id=state["user_id"],
            agent_id=state["agent_id"],
            messages=messages,
            response=state.get("response", ""),
        )
    except Exception as exc:  # noqa: BLE001 — writeback must never fail a reply
        logger.warning("Writeback node: failed to persist memories: %s", exc)
        updates = []
    stored = sum(1 for u in updates if u.get("action") in ("insert", "update"))
    return {
        "memory_updates": updates,
        "trace": append_trace(state, "writeback", "learned", stored=stored, candidates=len(updates)),
    }


# ----------------------------------------------------------------------
# Graph assembly
# ----------------------------------------------------------------------
def build_workflow():
    """Build and compile the agentic reasoning graph (conditional routing).

    After understanding the message, a ``router`` picks a route and conditional
    edges fork the flow:

    * ``crisis``   → crisis_response → safety → END   (no retrieval, no LLM)
    * ``direct``   → agent_loader → context_builder → … (skips retrieval)
    * ``retrieve`` / ``tool`` → agent_loader → self-correcting retrieval loop
      (plan_query → retrieve → grade → [reformulate → retrieve]* → generate)

    After the prompt is built, the ``tool`` route enters a ReAct tool loop
    (tool_agent → [tool_executor → tool_agent]*) while other routes generate
    once via ``llm``. Both feed the self-reflection loop, then the always-run
    deterministic safety gate.

    Every loop is bounded — retrieval by ``MAX_RETRIEVE_ITERS``, tools by
    ``MAX_TOOL_ITERS``, reflection by ``MAX_REFLECT_ITERS`` — so the graph
    always terminates and proceeds best-effort when a budget is exhausted.
    """
    builder = StateGraph(AgentState)

    builder.add_node("input", input_node)
    builder.add_node("intent", intent_node)
    builder.add_node("emotion", emotion_node)
    builder.add_node("router", router_node)
    builder.add_node("crisis_response", crisis_response_node)
    builder.add_node("agent_loader", agent_loader_node)
    builder.add_node("plan_query", plan_query_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("grade", grade_node)
    builder.add_node("reformulate", reformulate_node)
    builder.add_node("context_builder", context_builder_node)
    builder.add_node("prompt_builder", prompt_builder_node)
    builder.add_node("llm", llm_node)
    builder.add_node("tool_agent", tool_agent_node)
    builder.add_node("tool_executor", tool_executor_node)
    builder.add_node("reflect", reflect_node)
    builder.add_node("safety", safety_node)
    builder.add_node("response_finalizer", response_finalizer_node)
    builder.add_node("writeback", writeback_node)

    builder.add_edge(START, "input")
    builder.add_edge("input", "intent")
    builder.add_edge("intent", "emotion")
    builder.add_edge("emotion", "router")

    # Router fork: crisis takes the deterministic fast-path; everything else
    # proceeds into agent loading + generation.
    builder.add_conditional_edges(
        "router",
        route_from_router,
        {ROUTE_CRISIS: "crisis_response", "proceed": "agent_loader"},
    )

    # Crisis fast-path: deterministic response → safety → END (no LLM).
    builder.add_edge("crisis_response", "safety")

    # After loading the agent, `direct` turns skip retrieval; `retrieve`/`tool`
    # turns enter the self-correcting retrieval loop.
    builder.add_conditional_edges(
        "agent_loader",
        route_after_agent_loader,
        {"direct": "context_builder", "retrieve": "plan_query"},
    )

    # Self-correcting retrieval loop: plan → retrieve → grade → (reformulate → retrieve)*
    builder.add_edge("plan_query", "retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges(
        "grade",
        route_after_grade,
        {"reformulate": "reformulate", "generate": "context_builder"},
    )
    builder.add_edge("reformulate", "retrieve")

    builder.add_edge("context_builder", "prompt_builder")

    # Generation fork: the `tool` route enters a ReAct loop; others generate once.
    builder.add_conditional_edges(
        "prompt_builder",
        route_after_prompt,
        {"tool": "tool_agent", "generate": "llm"},
    )

    # ReAct tool loop: generate → (use_tool → execute → observe → generate)* → done.
    # Bounded by tool_iters; `done` yields a final draft that flows into reflect.
    builder.add_conditional_edges(
        "tool_agent",
        route_after_tool_agent,
        {"execute": "tool_executor", "done": "reflect"},
    )
    builder.add_edge("tool_executor", "tool_agent")

    # Self-reflection loop: the critic judges the draft before the safety gate.
    # `revise` loops back to re-retrieve + regenerate (bounded by reflect_iters);
    # `accept` proceeds to the deterministic safety engine.
    builder.add_edge("llm", "reflect")
    builder.add_conditional_edges(
        "reflect",
        route_after_reflect,
        {"revise": "plan_query", "accept": "safety"},
    )

    # Safety fork: crisis ends here (no writeback); normal turns finalize + learn.
    builder.add_conditional_edges(
        "safety",
        route_after_safety,
        {"end": END, "continue": "response_finalizer"},
    )
    builder.add_edge("response_finalizer", "writeback")
    builder.add_edge("writeback", END)

    return builder.compile()


def initial_state(user_id: str, agent_id: str, session_id: str, message: str) -> AgentState:
    """Construct a fresh, fully-initialized :class:`AgentState`."""
    return AgentState(
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
        message=message,
        intent=None,
        emotion=None,
        agent_config={},
        user_memory=[],
        conversation_memory=[],
        agent_memory=[],
        context={},
        prompt="",
        response=None,
        safety_flags={},
        memory_updates=[],
        # Agentic control layer (working memory for loops & decisions).
        route=None,
        search_query=None,
        retrieved=[],
        relevance_grade=None,
        retrieve_iters=0,
        tool_calls=[],
        tool_results=[],
        tool_iters=0,
        reflection=None,
        reflect_verdict=None,
        reflect_iters=0,
        trace=[],
    )


# Compiled, reusable graph instance.
workflow = build_workflow()


def run_workflow(user_id: str, agent_id: str, session_id: str, message: str) -> AgentState:
    """Convenience entry point: run the full pipeline for one message."""
    return workflow.invoke(
        initial_state(user_id, agent_id, session_id, message),
        config={"recursion_limit": RECURSION_LIMIT},
    )
