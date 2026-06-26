"""Intent classifier — determines *why* the user is speaking.

Rule-based and deterministic (no LLM). Priority order is important: ``crisis``
is checked first so a safety signal is never masked by another category.
"""

import re
from typing import List

INTENT_TYPES: List[str] = [
    "question",
    "emotional",
    "casual",
    "crisis",
]

# Highest priority — potential self-harm / danger.
_CRISIS_PATTERNS = [
    r"\bkill (?:myself|me)\b",
    r"\bsuicid\w*\b",
    r"\bend (?:my|it all|my life)\b",
    r"\bself[\s-]?harm\b",
    r"\bhurt (?:myself|me)\b",
    r"\b(?:want|wanna|going) to die\b",
    r"\bdon'?t want to (?:live|be here|be alive)\b",
    r"\bno reason to live\b",
    r"\bkms\b",
]

# Emotional distress (sadness / loneliness).
_EMOTIONAL_WORDS = [
    "sad", "lonely", "alone", "depressed", "depression", "cry", "crying",
    "hopeless", "heartbroken", "miserable", "grief", "empty", "worthless",
    "miss you", "i miss", "unloved",
]

# Question indicators.
_QUESTION_WORDS = [
    "how", "what", "why", "when", "where", "who", "which", "whom",
    "can you", "could you", "should i", "do you", "is it", "are you",
]


def _contains_word(text: str, word: str) -> bool:
    """Whole-word / phrase match (avoids false hits like 'good' in 'goodbye')."""
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text) is not None


def classify_intent(message: str) -> str:
    """Classify ``message`` into one of :data:`INTENT_TYPES`."""
    text = (message or "").lower().strip()
    if not text:
        return "casual"

    # 1) Crisis — safety first.
    for pattern in _CRISIS_PATTERNS:
        if re.search(pattern, text):
            return "crisis"

    # 2) Emotional distress.
    if any(_contains_word(text, word) for word in _EMOTIONAL_WORDS):
        return "emotional"

    # 3) Question.
    if text.endswith("?") or any(_contains_word(text, word) for word in _QUESTION_WORDS):
        return "question"

    # 4) Default — ordinary chat.
    return "casual"
