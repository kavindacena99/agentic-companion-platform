"""Chat service layer — single entry point for processing a chat turn.

Runs the full LangGraph pipeline (input -> intent -> emotion -> agent loader ->
memory retrieval -> context -> prompt -> LLM -> safety -> finalizer ->
writeback) and shapes the final API response. Memory writeback is triggered as
the final pipeline node, so by the time this returns the AI has already learned
from the exchange.

Every turn is measured: run metrics (route, loop counts, tools, provider,
latency) are logged, and — when the request sets ``debug`` and trace exposure is
enabled server-side — the decision ``trace`` + metrics are returned to the
caller for debugging.
"""

import logging
import os
import time
from typing import Any, Dict

from graph.workflow import run_workflow
from services.observability import log_run_metrics
from services.schemas.message import ChatMessage

logger = logging.getLogger("agent_core")

_TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}


def _trace_exposure_enabled() -> bool:
    """Whether the service may return decision traces (env-gated for prod safety)."""
    return os.getenv("AGENT_CORE_EXPOSE_TRACE", "false").strip().lower() in _TRUE_VALUES


def process_chat(message: ChatMessage) -> Dict[str, Any]:
    """Execute the end-to-end pipeline for one validated chat message."""
    logger.info(
        "process_chat user=%s agent=%s session=%s debug=%s",
        message.user_id,
        message.agent_id,
        message.session_id,
        getattr(message, "debug", False),
    )
    start = time.perf_counter()
    final_state = run_workflow(
        user_id=message.user_id,
        agent_id=message.agent_id,
        session_id=message.session_id,
        message=message.message,
    )
    latency_ms = (time.perf_counter() - start) * 1000.0

    # Always log metrics for observability; never leak the trace by default.
    metrics = log_run_metrics(final_state, latency_ms)

    result: Dict[str, Any] = {
        "response": final_state.get("response", ""),
        "emotion": final_state.get("emotion"),
        "intent": final_state.get("intent"),
    }
    if getattr(message, "debug", False) and _trace_exposure_enabled():
        result["trace"] = final_state.get("trace", [])
        result["metrics"] = metrics
    return result
