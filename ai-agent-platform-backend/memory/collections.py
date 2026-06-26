"""Memory collection definitions and accessors.

agent-core uses four long-term memory collections, each with a clear purpose:

* ``user_memory``           — user preferences, facts, long-term profile info
* ``conversation_memory``   — conversation summaries, past interactions
* ``emotional_memory``      — emotional events, mood patterns
* ``agent_behavior_memory`` — behavior.txt chunks, personality / tone rules

Collections are created on demand (get-or-create) and use cosine distance,
which matches the unit-normalized embeddings produced by the embedding layer.
We pass ``embedding_function=None`` because embeddings are always supplied
explicitly by the writer/retriever — this keeps the engine fully offline.
"""

import logging
from typing import Dict

from chromadb.api.models.Collection import Collection

from memory.chroma_client import get_client

logger = logging.getLogger("agent_core")

# Canonical collection names.
USER_MEMORY = "user_memory"
CONVERSATION_MEMORY = "conversation_memory"
EMOTIONAL_MEMORY = "emotional_memory"
AGENT_BEHAVIOR_MEMORY = "agent_behavior_memory"

COLLECTIONS = (
    USER_MEMORY,
    CONVERSATION_MEMORY,
    EMOTIONAL_MEMORY,
    AGENT_BEHAVIOR_MEMORY,
)

# Default memory_type tag attached to records written to each collection.
COLLECTION_MEMORY_TYPE = {
    USER_MEMORY: "user",
    CONVERSATION_MEMORY: "conversation",
    EMOTIONAL_MEMORY: "emotional",
    AGENT_BEHAVIOR_MEMORY: "behavior",
}


def get_collection(name: str) -> Collection:
    """Return (creating if needed) the named memory collection."""
    if name not in COLLECTIONS:
        raise ValueError(
            f"Unknown memory collection '{name}'. Valid: {', '.join(COLLECTIONS)}"
        )
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        embedding_function=None,
        metadata={"hnsw:space": "cosine"},
    )


def init_collections() -> Dict[str, Collection]:
    """Ensure all four collections exist; return them keyed by name."""
    collections = {name: get_collection(name) for name in COLLECTIONS}
    logger.info("Initialized memory collections: %s", ", ".join(COLLECTIONS))
    return collections
