"""ChromaDB-backed agentic memory engine (long-term AI memory).

Public high-level API lives in :mod:`memory.memory_service`. Lower-level pieces
(client, collections, embeddings, writer, retriever) are available for advanced
use but most callers should go through the service layer.
"""

from memory.collections import (
    AGENT_BEHAVIOR_MEMORY,
    CONVERSATION_MEMORY,
    EMOTIONAL_MEMORY,
    USER_MEMORY,
    init_collections,
)
from memory.memory_service import (
    get_relevant_memories,
    save_agent_behavior_memory,
    save_conversation_memory,
    save_emotional_memory,
    save_user_memory,
)

__all__ = [
    "USER_MEMORY",
    "CONVERSATION_MEMORY",
    "EMOTIONAL_MEMORY",
    "AGENT_BEHAVIOR_MEMORY",
    "init_collections",
    "save_user_memory",
    "save_conversation_memory",
    "save_emotional_memory",
    "save_agent_behavior_memory",
    "get_relevant_memories",
]
