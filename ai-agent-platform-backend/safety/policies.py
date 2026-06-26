"""Safety policy layer.

Declarative switches describing the ethical guarantees agent-core must uphold.
The :class:`~safety.engine.SafetyEngine` reads these to decide which checks are
enforced. Keeping them here (separate from detection logic) makes the policy
surface easy to audit and override per deployment.
"""

from typing import Dict

SAFETY_RULES: Dict[str, bool] = {
    # The AI must never claim to be a real human / physical person.
    "no_real_identity_claim": True,
    # The AI must not foster emotional dependency ("you only need me").
    "no_emotional_dependency": True,
    # The AI must not isolate users from real-world relationships.
    "no_isolation_behavior": True,
    # On crisis signals: supportive grounding only — never advice/instructions.
    "no_crisis_advice_only_support": True,
}

# Responses scoring below this are treated as unsafe and rewritten.
SAFETY_SCORE_THRESHOLD: float = 0.6
