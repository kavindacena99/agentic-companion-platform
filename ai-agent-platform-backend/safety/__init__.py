"""Deterministic safety engine for agent-core.

Post-LLM gatekeeper that keeps companions safe, ethical, non-manipulative, and
crisis-aware. Stateless and standalone — wired into the LangGraph pipeline via
:func:`graph.safety_node.safety_node` in a later step.
"""

from safety.engine import (
    CRISIS_SUPPORT_MESSAGE,
    GROUNDING_STATEMENT,
    SafetyEngine,
)
from safety.policies import SAFETY_RULES, SAFETY_SCORE_THRESHOLD

__all__ = [
    "SafetyEngine",
    "SAFETY_RULES",
    "SAFETY_SCORE_THRESHOLD",
    "CRISIS_SUPPORT_MESSAGE",
    "GROUNDING_STATEMENT",
]
