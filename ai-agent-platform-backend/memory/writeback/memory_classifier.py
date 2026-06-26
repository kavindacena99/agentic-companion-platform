"""Memory classifier.

Maps an extracted memory candidate to the ChromaDB collection it belongs in:
``user_memory``, ``conversation_memory`` or ``emotional_memory``.
"""

from typing import Dict

from memory.collections import (
    CONVERSATION_MEMORY,
    EMOTIONAL_MEMORY,
    USER_MEMORY,
)

_EMOTIONAL = {"emotional", "emotion", "mood", "feeling"}
_CONVERSATION = {"conversation", "summary", "interaction", "dialogue"}
_USER = {"user_fact", "fact", "preference", "profile", "user"}


def classify_memory(item: Dict) -> str:
    """Return the target collection name for ``item`` based on its ``type``."""
    item_type = (item.get("type") or "").lower()
    if item_type in _EMOTIONAL:
        return EMOTIONAL_MEMORY
    if item_type in _CONVERSATION:
        return CONVERSATION_MEMORY
    if item_type in _USER:
        return USER_MEMORY
    # Sensible default: treat unknown items as conversation context.
    return CONVERSATION_MEMORY
