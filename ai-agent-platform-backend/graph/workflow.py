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
from graph.state import AgentState, append_trace
from llm.llm_router import route_llm
from memory.memory_service import get_relevant_memories
from memory.writeback.writeback_engine import process_writeback
from services.agent_loader import AgentLoaderError, AgentLoaderService
from services.classifiers import classify_intent, detect_emotion

logger = logging.getLogger("agent_core")


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
# NODE 5 — Memory retrieval (integrates Step 4, never modifies it)
# ----------------------------------------------------------------------
def memory_retriever_node(state: AgentState) -> Dict[str, Any]:
    context = dict(state.get("context") or {})
    try:
        memories = get_relevant_memories(
            query=state.get("message", ""),
            user_id=state["user_id"],
            agent_id=state["agent_id"],
            top_k=5,
        )
    except Exception as exc:  # noqa: BLE001 — memory must never crash reasoning
        logger.warning("Memory node: retrieval failed: %s", exc)
        memories = {}

    context["emotional_memory"] = memories.get("emotional_memory", [])
    return {
        "user_memory": memories.get("user_memory", []),
        "conversation_memory": memories.get("conversation_memory", []),
        "agent_memory": memories.get("agent_behavior_memory", []),
        "context": context,
    }


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
    return {"memory_updates": updates}


# ----------------------------------------------------------------------
# Graph assembly
# ----------------------------------------------------------------------
def build_workflow():
    """Build and compile the linear reasoning graph."""
    builder = StateGraph(AgentState)

    builder.add_node("input", input_node)
    builder.add_node("intent", intent_node)
    builder.add_node("emotion", emotion_node)
    builder.add_node("agent_loader", agent_loader_node)
    builder.add_node("memory_retriever", memory_retriever_node)
    builder.add_node("context_builder", context_builder_node)
    builder.add_node("prompt_builder", prompt_builder_node)
    builder.add_node("llm", llm_node)
    builder.add_node("safety", safety_node)
    builder.add_node("response_finalizer", response_finalizer_node)
    builder.add_node("writeback", writeback_node)

    builder.add_edge(START, "input")
    builder.add_edge("input", "intent")
    builder.add_edge("intent", "emotion")
    builder.add_edge("emotion", "agent_loader")
    builder.add_edge("agent_loader", "memory_retriever")
    builder.add_edge("memory_retriever", "context_builder")
    builder.add_edge("context_builder", "prompt_builder")
    builder.add_edge("prompt_builder", "llm")
    builder.add_edge("llm", "safety")
    builder.add_edge("safety", "response_finalizer")
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
        reflection=None,
        reflect_iters=0,
        trace=[],
    )


# Compiled, reusable graph instance.
workflow = build_workflow()


def run_workflow(user_id: str, agent_id: str, session_id: str, message: str) -> AgentState:
    """Convenience entry point: run the full pipeline for one message."""
    return workflow.invoke(initial_state(user_id, agent_id, session_id, message))
