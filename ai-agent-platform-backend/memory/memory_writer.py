"""Memory writer — the storage engine.

Generates an embedding for a piece of content and persists it into the correct
ChromaDB collection with normalized, filterable metadata.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from memory.collections import COLLECTION_MEMORY_TYPE, get_collection
from memory.embeddings import generate_embedding

logger = logging.getLogger("agent_core")

# Metadata values Chroma accepts directly. Anything else is coerced to str.
_SCALAR_TYPES = (str, int, float, bool)


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce metadata into Chroma-compatible scalar values (drop ``None``)."""
    clean: Dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        clean[key] = value if isinstance(value, _SCALAR_TYPES) else str(value)
    return clean


def store_memory(
    collection_name: str,
    user_id: str,
    agent_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Embed ``content`` and store it in ``collection_name``.

    Always attaches ``user_id``, ``agent_id``, ``timestamp`` and ``memory_type``
    so every record is filterable. Returns the generated record id.
    """
    collection = get_collection(collection_name)

    record_metadata: Dict[str, Any] = dict(metadata or {})
    record_metadata.setdefault(
        "memory_type", COLLECTION_MEMORY_TYPE.get(collection_name, collection_name)
    )
    record_metadata["user_id"] = user_id
    record_metadata["agent_id"] = agent_id
    record_metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

    record_id = str(uuid.uuid4())
    embedding = generate_embedding(content)

    collection.add(
        ids=[record_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[_sanitize_metadata(record_metadata)],
    )

    logger.debug(
        "Stored memory %s in %s (user=%s agent=%s type=%s)",
        record_id,
        collection_name,
        user_id,
        agent_id,
        record_metadata["memory_type"],
    )
    return record_id
