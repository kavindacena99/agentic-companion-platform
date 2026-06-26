"""LangGraph shared state for the Companio agent-core.

``AgentState`` is the single source of truth that flows through every node in
the LangGraph workflow. Nodes read from and write to this object — it is the
only thing passed between them.

This module defines *structure only*. There is no business logic here: no LLM
calls, no memory/vector-store access, and no dependency on the main backend.
"""

from typing import Any, Dict, List, Optional, TypedDict


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
