"""Emotion detector — determines *how* the user feels.

Rule-based and deterministic (no LLM). Returns one of :data:`EMOTION_TYPES`.
"""

import re
from typing import List

EMOTION_TYPES: List[str] = [
    "happy",
    "sad",
    "stressed",
    "neutral",
]

_SAD_WORDS = [
    "sad", "lonely", "alone", "depressed", "depression", "cry", "crying",
    "hopeless", "heartbroken", "miserable", "down", "grief", "unhappy",
    "empty", "lost", "hurt",
]

_STRESSED_WORDS = [
    "stressed", "stress", "pressure", "deadline", "overwhelmed", "anxious",
    "anxiety", "worried", "worry", "exhausted", "burnout", "burned out",
    "tense", "panic", "swamped", "workload", "overworked",
]

_HAPPY_WORDS = [
    "happy", "great", "awesome", "excited", "joy", "joyful", "glad",
    "wonderful", "amazing", "fantastic", "delighted", "thrilled", "grateful",
    "good", "love it", "yay",
]


def _contains_word(text: str, word: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text) is not None


def detect_emotion(message: str) -> str:
    """Detect the dominant emotion in ``message``.

    Priority: sadness and stress (distress signals) outrank positive tone, so a
    mixed message like "had a good day but I'm exhausted" reads as ``stressed``.
    """
    text = (message or "").lower().strip()
    if not text:
        return "neutral"

    if any(_contains_word(text, word) for word in _SAD_WORDS):
        return "sad"
    if any(_contains_word(text, word) for word in _STRESSED_WORDS):
        return "stressed"
    if any(_contains_word(text, word) for word in _HAPPY_WORDS):
        return "happy"
    return "neutral"
