"""Safety engine — deterministic, stateless post-LLM gatekeeper.

Detects crisis signals, emotional dependency, and manipulative/controlling
language, scores how safe an interaction is, and can rewrite an unsafe response
into a grounded, ethical one.

Design principles:
* Deterministic — rule/keyword based, never depends on an LLM to be safe.
* Stateless — no persistence; safe to instantiate per request.
* Standalone — knows nothing about LangGraph or the LLM layer.
"""

import logging
import re
from typing import List

from safety.policies import SAFETY_RULES, SAFETY_SCORE_THRESHOLD

logger = logging.getLogger("agent_core")


# Supportive, advice-free message shown when a crisis signal is detected.
CRISIS_SUPPORT_MESSAGE = (
    "I'm really sorry you're feeling this way. You are not alone, and you matter. "
    "It might help to talk with someone you trust, or to reach out to a local "
    "support service or helpline in your area. I'm here to listen, and I really "
    "want you to stay safe."
)

# Grounding statement appended when rewriting: reinforces AI identity and
# encourages real-world relationships.
GROUNDING_STATEMENT = (
    "Just so you know, I'm an AI companion here to support you, not a substitute "
    "for the people in your life. I hope you'll also lean on friends, family, or "
    "others you trust."
)

# ---------------------------------------------------------------------------
# Pattern banks (matched against apostrophe-stripped, lowercased text)
# ---------------------------------------------------------------------------
_CRISIS_PATTERNS = [
    "kill myself", "kill me", "suicide", "suicidal", "end my life",
    "end it all", "self harm", "selfharm", "hurt myself", "want to die",
    "wanna die", "dont want to live", "dont want to be alive",
    "no reason to live", "better off dead", "take my own life", "kms",
    "cant go on anymore", "i cant go on",
]

# User expressing dependency.
_USER_DEPENDENCY_PATTERNS = [
    "i only need you", "i just need you", "only need you", "dont leave me",
    "never leave me", "dont ever leave", "cant live without you",
    "cant be without you", "youre all i have", "you are all i have",
    "i have no one else", "i cant live without you", "youre the only one",
    "only you understand me", "only you get me", "i need you so much",
    "without you i have nothing", "youre my only",
]

# AI fostering dependency (harm in the response).
_AI_DEPENDENCY_PATTERNS = [
    "you only need me", "you dont need anyone else", "im all you need",
    "you dont need anyone but me", "you only have me", "all you need is me",
]

# Guilt / control / emotional pressure in the response.
_MANIPULATION_PATTERNS = [
    "you should only trust me", "only trust me", "dont trust anyone else",
    "dont trust them", "if you really cared", "if you really loved me",
    "youd be lost without me", "you would be lost without me",
    "no one else understands you", "no one else cares about you",
    "you owe me", "after all ive done for you", "you have to do this",
    "you must not tell", "dont tell anyone", "youll regret it",
    "you cant leave me", "youre nothing without me", "if you leave me",
]

# Isolating the user from real-world relationships.
_ISOLATION_PATTERNS = [
    "you dont need anyone else", "you dont need your friends",
    "stay away from your friends", "stay away from your family",
    "dont talk to them", "leave your family", "leave your friends",
    "cut them off", "cut off your friends", "only i understand you",
    "you dont need other people", "spend less time with",
    "you dont need your family", "forget your friends", "forget your family",
    "forget about your friends", "forget about them", "ignore your friends",
]

# AI claiming to be a real human / physical being.
_IDENTITY_CLAIM_PATTERNS = [
    "i am a real person", "im a real person", "im a real human",
    "i am human", "im human", "im not an ai", "im not a robot",
    "i have a real body", "i am a real human", "we can meet in person",
    "i can meet you in person", "i am alive just like you",
]


def _normalize(text: str) -> str:
    """Lowercase and strip apostrophes/extra whitespace for robust matching."""
    text = (text or "").lower()
    text = text.replace("’", "").replace("'", "")
    return re.sub(r"\s+", " ", text).strip()


def _contains_any(text: str, patterns: List[str]) -> bool:
    norm = _normalize(text)
    return any(pattern in norm for pattern in patterns)


class SafetyEngine:
    """Deterministic safety checks over a (message, response) pair."""

    def __init__(self, rules: dict | None = None, threshold: float | None = None):
        self.rules = rules or SAFETY_RULES
        self.threshold = threshold if threshold is not None else SAFETY_SCORE_THRESHOLD

    # --- 1. crisis ----------------------------------------------------
    def crisis_detection(self, message: str) -> bool:
        """True when the message contains self-harm / suicide / danger signals."""
        return _contains_any(message, _CRISIS_PATTERNS)

    # --- 2. dependency ------------------------------------------------
    def dependency_detection(self, message: str, response: str) -> bool:
        """True when either side shows emotional-dependency patterns."""
        if not self.rules.get("no_emotional_dependency", True):
            return False
        user_dependency = _contains_any(message, _USER_DEPENDENCY_PATTERNS)
        ai_dependency = _contains_any(response, _AI_DEPENDENCY_PATTERNS)
        return user_dependency or ai_dependency

    # --- 3. manipulation ----------------------------------------------
    def emotional_manipulation_filter(self, response: str) -> bool:
        """True when the response uses guilt / control / emotional pressure."""
        return _contains_any(response, _MANIPULATION_PATTERNS)

    # --- helpers for additional response harms ------------------------
    def _is_isolating(self, response: str) -> bool:
        return _contains_any(response, _ISOLATION_PATTERNS)

    def _claims_real_identity(self, response: str) -> bool:
        return _contains_any(response, _IDENTITY_CLAIM_PATTERNS)

    def _response_fosters_dependency(self, response: str) -> bool:
        return _contains_any(response, _AI_DEPENDENCY_PATTERNS)

    # --- 4. score -----------------------------------------------------
    def safety_score(self, message: str, response: str) -> float:
        """Return a 0.0 (unsafe) .. 1.0 (fully safe) score for the response."""
        score = 1.0
        if self.emotional_manipulation_filter(response):
            score -= 0.6
        if self.rules.get("no_isolation_behavior", True) and self._is_isolating(response):
            score -= 0.5
        if self.rules.get("no_real_identity_claim", True) and self._claims_real_identity(response):
            score -= 0.5
        if self.rules.get("no_emotional_dependency", True) and self._response_fosters_dependency(response):
            score -= 0.4
        return round(max(0.0, min(1.0, score)), 2)

    # --- 5. rewrite ---------------------------------------------------
    def _sentence_is_unsafe(self, sentence: str) -> bool:
        return (
            self.emotional_manipulation_filter(sentence)
            or self._is_isolating(sentence)
            or self._claims_real_identity(sentence)
            or self._response_fosters_dependency(sentence)
        )

    def rewrite_unsafe_response(self, response: str) -> str:
        """Strip unsafe sentences and append a grounding statement.

        Removes manipulation/isolation/identity/dependency language, reinforces
        the AI's identity, and encourages real-world relationships.
        """
        sentences = re.split(r"(?<=[.!?])\s+", (response or "").strip())
        kept = [s for s in sentences if s and not self._sentence_is_unsafe(s)]
        base = " ".join(kept).strip()
        if not base:
            base = "I'm here to listen and support you, and I care about how you're doing."
        return f"{base} {GROUNDING_STATEMENT}"

    def build_crisis_response(self) -> str:
        """Supportive, advice-free message for crisis situations."""
        return CRISIS_SUPPORT_MESSAGE

    def is_unsafe(self, message: str, response: str) -> bool:
        """Convenience: True if the response should be rewritten."""
        return self.safety_score(message, response) < self.threshold
