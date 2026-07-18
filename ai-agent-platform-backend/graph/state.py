"""LangGraph shared state for the Companio agent-core.

``AgentState`` is the single source of truth that flows through every node in
the LangGraph workflow. Nodes read from and write to this object — it is the
only thing passed between them.

This module defines *structure only*. There is no business logic here: no LLM
calls, no memory/vector-store access, and no dependency on the main backend.
Alongside the state shape it also holds the agentic **control scaffolding**: the
loop-bound constants and a small ``append_trace`` helper decision nodes use to
record what they decided.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

# ─────────────────────────────────────────────────────────────────────
# Loop bounds
# ─────────────────────────────────────────────────────────────────────
# Hard caps on the agentic loops so the graph can never spin forever. A loop
# node compares the matching ``*_iters`` counter against these before looping
# back; on reaching the cap it must fall through to the next stage instead.
MAX_RETRIEVE_ITERS = 3
MAX_REFLECT_ITERS = 2
# Cap on ReAct tool rounds (generate → use_tool → observe) per turn.
MAX_TOOL_ITERS = 3


class AgentState(TypedDict):
    """Unified state that travels through the entire agent reasoning graph."""

    # ─────────────────────────────
    # INPUT LAYER
    # ─────────────────────────────
    user_id: str
    agent_id: str
    session_id: str
    message: str

    # ─────────────────────────────
    # UNDERSTANDING LAYER
    # ─────────────────────────────
    intent: Optional[str]
    emotion: Optional[str]

    # ─────────────────────────────
    # AGENT LAYER
    # ─────────────────────────────
    agent_config: Dict[str, Any]

    # ─────────────────────────────
    # MEMORY LAYER (CHROMADB OUTPUT)
    # ─────────────────────────────
    user_memory: List[Dict[str, Any]]
    conversation_memory: List[Dict[str, Any]]
    agent_memory: List[Dict[str, Any]]

    # ─────────────────────────────
    # CONTEXT LAYER
    # ─────────────────────────────
    context: Dict[str, Any]

    # ─────────────────────────────
    # PROMPT LAYER
    # ─────────────────────────────
    prompt: str

    # ─────────────────────────────
    # OUTPUT LAYER
    # ─────────────────────────────
    response: Optional[str]

    # ─────────────────────────────
    # SAFETY LAYER
    # ─────────────────────────────
    safety_flags: Dict[str, Any]

    # ─────────────────────────────
    # MEMORY WRITEBACK LAYER
    # ─────────────────────────────
    memory_updates: List[Dict[str, Any]]

    # ─────────────────────────────
    # AGENTIC CONTROL LAYER (working memory for loops & decisions)
    # ─────────────────────────────
    # Routing decision emitted by a decision node (e.g. which branch to take).
    route: Optional[str]
    # (Re)formulated query used to drive corrective retrieval.
    search_query: Optional[str]
    # Raw candidates returned by the latest retrieval pass (scored memories).
    retrieved: List[Dict[str, Any]]
    # Grader verdict on ``retrieved`` (e.g. "relevant" / "insufficient").
    relevance_grade: Optional[str]
    # How many retrieval passes have run — bounded by ``MAX_RETRIEVE_ITERS``.
    retrieve_iters: int
    # Tool invocations the agent requested this turn (pending execution).
    tool_calls: List[Dict[str, Any]]
    # Observations returned for executed tools (the ReAct scratchpad results).
    tool_results: List[Dict[str, Any]]
    # How many ReAct tool rounds have run — bounded by ``MAX_TOOL_ITERS``.
    tool_iters: int
    # Self-critique of a draft response produced by a reflection node.
    reflection: Optional[str]
    # Reflection verdict on the current draft ("accept" / "revise").
    reflect_verdict: Optional[str]
    # How many reflection passes have run — bounded by ``MAX_REFLECT_ITERS``.
    reflect_iters: int
    # Ordered decision trace: one entry per decision, for observability.
    trace: List[Dict[str, Any]]


def append_trace(
    state: "AgentState", node: str, decision: str, **details: Any
) -> List[Dict[str, Any]]:
    """Return ``state``'s trace with one decision entry appended.

    Decision nodes call this and include the result in their partial state
    update so the graph accumulates an ordered, inspectable record of what each
    node decided::

        return {"trace": append_trace(state, "grade", "insufficient", score=0.2)}

    The input state is never mutated — a new list is returned. ``details`` are
    stored under an optional ``details`` key for any decision-specific context.
    """
    trace = list(state.get("trace") or [])
    entry: Dict[str, Any] = {
        "step": len(trace) + 1,
        "node": node,
        "decision": decision,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        entry["details"] = details
    trace.append(entry)
    return trace
