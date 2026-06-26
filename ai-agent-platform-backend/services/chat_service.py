"""Chat service layer — single entry point for processing a chat turn.

Runs the full LangGraph pipeline (input -> intent -> emotion -> agent loader ->
memory retrieval -> context -> prompt -> LLM -> safety -> finalizer ->
writeback) and shapes the final API response. Memory writeback is triggered as
the final pipeline node, so by the time this returns the AI has already learned
from the exchange.
"""

import logging
from typing import Any, Dict

from graph.workflow import run_workflow
from services.schemas.message import ChatMessage

logger = logging.getLogger("agent_core")


def process_chat(message: ChatMessage) -> Dict[str, Any]:
    """Execute the end-to-end pipeline for one validated chat message."""
    logger.info(
        "process_chat user=%s agent=%s session=%s",
        message.user_id,
        message.agent_id,
        message.session_id,
    )
    final_state = run_workflow(
        user_id=message.user_id,
        agent_id=message.agent_id,
        session_id=message.session_id,
        message=message.message,
    )
    return {
        "response": final_state.get("response", ""),
        "emotion": final_state.get("emotion"),
        "intent": final_state.get("intent"),
    }
