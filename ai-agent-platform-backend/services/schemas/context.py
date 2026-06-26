"""Prompt context schema (LLM input preparation).

Aggregates everything needed to build the final LLM prompt: the system
instruction, agent persona, retrieved memories, and the current understanding
of the user's turn. Structure only — no prompt building or LLM calls here.
"""

from typing import Any, Dict, List

from pydantic import BaseModel


class PromptContext(BaseModel):
    system_prompt: str
    agent_persona: Dict[str, Any]

    user_memory: List[Dict[str, Any]]
    conversation_memory: List[Dict[str, Any]]
    agent_memory: List[Dict[str, Any]]

    emotion: str
    intent: str

    user_message: str
