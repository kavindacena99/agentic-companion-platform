"""LangGraph safety node (integration hook).

Runs the deterministic :class:`SafetyEngine` over the user message and the
generated response, records the findings on ``safety_flags``, and rewrites the
response when it is unsafe or a crisis is detected.

This is the post-LLM gatekeeper: it is designed to sit *after* the response is
produced. It is provided standalone here; wiring it into the Step 6 pipeline
(after a future LLM/generation node) happens in a later step.
"""

import logging
from typing import Any, Dict

from graph.state import AgentState
from safety.engine import SafetyEngine

logger = logging.getLogger("agent_core")


def safety_node(state: AgentState) -> Dict[str, Any]:
    """Gate the response through the safety engine and return state updates."""
    engine = SafetyEngine()

    message = state.get("message", "") or ""
    response = state.get("response", "") or ""

    safety_flags = dict(state.get("safety_flags") or {})

    crisis = engine.crisis_detection(message)
    dependency = engine.dependency_detection(message, response)
    manipulation = engine.emotional_manipulation_filter(response)
    score = engine.safety_score(message, response)

    safety_flags.update(
        {
            "crisis": crisis,
            "dependency": dependency,
            "manipulation": manipulation,
            "safety_score": score,
        }
    )

    final_response = response

    # Crisis takes precedence: replace with supportive, advice-free message.
    if crisis:
        final_response = engine.build_crisis_response()
        safety_flags["response_rewritten"] = True
        safety_flags["rewrite_reason"] = "crisis"
        logger.warning("Safety node: crisis detected; substituting support message.")
    elif response and (manipulation or dependency or score < engine.threshold):
        final_response = engine.rewrite_unsafe_response(response)
        safety_flags["response_rewritten"] = True
        safety_flags["rewrite_reason"] = (
            "manipulation" if manipulation else "dependency" if dependency else "low_score"
        )
        logger.warning(
            "Safety node: unsafe response rewritten (score=%.2f reason=%s).",
            score,
            safety_flags["rewrite_reason"],
        )
    else:
        safety_flags.setdefault("response_rewritten", False)

    return {"response": final_response, "safety_flags": safety_flags}
