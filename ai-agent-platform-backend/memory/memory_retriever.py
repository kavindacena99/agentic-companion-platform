"""Memory retriever — similarity search.

Converts a query into an embedding and runs a filtered similarity search
against a ChromaDB collection, always scoped to a single ``user_id`` /
``agent_id`` so memories never leak across users or agents.
"""

import logging
from typing import Any, Dict, List, Optional

from memory.collections import get_collection
from memory.embeddings import generate_embedding

logger = logging.getLogger("agent_core")


def _build_where(user_id: str, agent_id: str, extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a Chroma ``where`` filter (uses ``$and`` for multiple conditions)."""
    conditions: List[Dict[str, Any]] = [
        {"user_id": user_id},
        {"agent_id": agent_id},
    ]
    if extra:
        conditions.extend({key: value} for key, value in extra.items())
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def search_memory(
    collection_name: str,
    query: str,
    user_id: str,
    agent_id: str,
    top_k: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return up to ``top_k`` memories most similar to ``query``.

    Results are filtered by ``user_id`` and ``agent_id`` (plus any extra
    ``where`` conditions) and ranked by similarity (closest first). Each result
    is ``{id, content, metadata, distance}``.
    """
    collection = get_collection(collection_name)

    # Nothing stored yet → nothing to search.
    if collection.count() == 0:
        return []

    query_embedding = generate_embedding(query)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=_build_where(user_id, agent_id, where),
    )

    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    ranked: List[Dict[str, Any]] = []
    for index, record_id in enumerate(ids):
        ranked.append(
            {
                "id": record_id,
                "content": documents[index] if index < len(documents) else None,
                "metadata": metadatas[index] if index < len(metadatas) else {},
                "distance": distances[index] if index < len(distances) else None,
            }
        )

    logger.debug(
        "search_memory(%s) user=%s agent=%s -> %d hits",
        collection_name,
        user_id,
        agent_id,
        len(ranked),
    )
    return ranked
