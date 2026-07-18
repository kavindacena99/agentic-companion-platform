"""Observability helpers — turn the agent's working state into metrics.

The graph already records a step-by-step decision ``trace`` (see
``graph/state.py``). This module distills the final :class:`AgentState` into a
compact metrics summary — route, grades, loop counts, tools used, provider and
latency — that is logged for every turn and, behind a debug flag, returned to
the caller alongside the raw trace.

Pure and dependency-light (no Django, no LLM, no DB) so it is trivially testable.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agent_core")


def summarize_run(state: Dict[str, Any], latency_ms: Optional[float] = None) -> Dict[str, Any]:
    """Distill a finished run's :class:`AgentState` into a metrics dict."""
    context = state.get("context") or {}
    tool_results = state.get("tool_results") or []
    safety_flags = state.get("safety_flags") or {}

    metrics: Dict[str, Any] = {
        "route": state.get("route"),
        "intent": state.get("intent"),
        "emotion": state.get("emotion"),
        "relevance_grade": state.get("relevance_grade"),
        "reflect_verdict": state.get("reflect_verdict"),
        "loops": {
            "retrieve_iters": int(state.get("retrieve_iters") or 0),
            "reflect_iters": int(state.get("reflect_iters") or 0),
            "tool_iters": int(state.get("tool_iters") or 0),
        },
        "tools_used": [item.get("name") for item in tool_results],
        "provider": context.get("llm_provider"),
        "llm_ok": context.get("llm_ok"),
        "safety": {
            "crisis": bool(safety_flags.get("crisis")),
            "response_rewritten": bool(safety_flags.get("response_rewritten")),
            "rewrite_reason": safety_flags.get("rewrite_reason"),
        },
        "trace_steps": len(state.get("trace") or []),
    }
    if latency_ms is not None:
        metrics["latency_ms"] = round(float(latency_ms), 1)
    return metrics


def log_run_metrics(
    state: Dict[str, Any],
    latency_ms: Optional[float] = None,
    log: logging.Logger = logger,
) -> Dict[str, Any]:
    """Log the run metrics at INFO and return the summary dict."""
    metrics = summarize_run(state, latency_ms)
    log.info(
        "chat metrics: route=%s loops=%s tools=%s provider=%s rewritten=%s latency_ms=%s",
        metrics["route"],
        metrics["loops"],
        metrics["tools_used"],
        metrics["provider"],
        metrics["safety"]["response_rewritten"],
        metrics.get("latency_ms"),
    )
    return metrics


def trace_summary(trace: Optional[List[Dict[str, Any]]]) -> List[str]:
    """Compact ``node:decision`` labels for a trace (handy for logs/tests)."""
    return [f"{entry.get('node')}:{entry.get('decision')}" for entry in (trace or [])]
