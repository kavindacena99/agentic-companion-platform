"""Conversation summarizer.

Condenses a chat exchange into a short memory summary and captures the dominant
emotional tone. Deterministic (no LLM required) so writeback is cheap and
reliable; a future step may optionally upgrade this to an LLM summary.
"""

from typing import Dict, List

from services.classifiers import detect_emotion


def _pairs(messages: List[Dict]) -> List[tuple]:
    pairs = []
    for entry in messages or []:
        role = (entry.get("role") or "user").lower()
        content = (entry.get("content") or "").strip()
        if content:
            pairs.append((role, content))
    return pairs


def summarize_conversation(messages: List[Dict]) -> str:
    """Return a short summary string capturing focus + emotional tone."""
    pairs = _pairs(messages)
    if not pairs:
        return ""

    user_messages = [content for role, content in pairs if role == "user"]
    joined = " ".join(user_messages)
    emotion = detect_emotion(joined) if joined else "neutral"

    latest_focus = user_messages[-1] if user_messages else pairs[-1][1]
    latest_focus = latest_focus[:160].strip()

    return (
        f"Conversation summary (emotional tone: {emotion}). "
        f"Latest user focus: {latest_focus}"
    )
