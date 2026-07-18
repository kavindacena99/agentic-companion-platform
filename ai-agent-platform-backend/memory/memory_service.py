"""Memory service layer — the single high-level interface to the memory engine.

The rest of the system should use this module rather than touching collections,
the writer, or the retriever directly. It exposes simple ``save_*`` helpers for
each memory type and one ``get_relevant_memories`` entry point for retrieval.

No LLM calls and no Main Backend calls live here — this is a pure memory layer.
"""

import logging
from typing import Any, Dict, List, Optional

from memory.collections import (
    AGENT_BEHAVIOR_MEMORY,
    CONVERSATION_MEMORY,
    EMOTIONAL_MEMORY,
    USER_MEMORY,
)
from memory.memory_retriever import DEFAULT_ALPHA, search_memory
from memory.memory_writer import store_memory
from memory.structured.canonical_store import get_canonical_store

logger = logging.getLogger("agent_core")


# ----------------------------------------------------------------------
# Write helpers — one per collection
# ----------------------------------------------------------------------
def save_user_memory(
    user_id: str, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Store a long-term user fact / preference / profile detail."""
    return store_memory(USER_MEMORY, user_id, agent_id, content, metadata)


def save_conversation_memory(
    user_id: str, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Store a conversation summary / past interaction / dialogue context."""
    return store_memory(CONVERSATION_MEMORY, user_id, agent_id, content, metadata)


def save_emotional_memory(
    user_id: str, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Store an emotional event / mood pattern."""
    return store_memory(EMOTIONAL_MEMORY, user_id, agent_id, content, metadata)


def save_agent_behavior_memory(
    user_id: str, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Store an agent behavior / personality / tone chunk."""
    return store_memory(AGENT_BEHAVIOR_MEMORY, user_id, agent_id, content, metadata)


# ----------------------------------------------------------------------
# Read helper — retrieve relevant memories across collections
# ----------------------------------------------------------------------
def get_relevant_memories(
    query: str,
    user_id: str,
    agent_id: str,
    top_k: int = 5,
    collections: Optional[List[str]] = None,
    hybrid: bool = True,
    alpha: float = DEFAULT_ALPHA,
) -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve the most relevant memories for ``query``.

    Searches each requested collection (all four by default) scoped to the given
    user and agent, using hybrid dense + lexical (BM25) re-ranking. Returns a
    dict keyed by collection name; each memory carries a normalized ``relevance``
    score in ``[0, 1]`` for a downstream grader to consume.
    """
    target_collections = collections or [
        USER_MEMORY,
        CONVERSATION_MEMORY,
        EMOTIONAL_MEMORY,
        AGENT_BEHAVIOR_MEMORY,
    ]

    results: Dict[str, List[Dict[str, Any]]] = {}
    for name in target_collections:
        results[name] = search_memory(
            collection_name=name,
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            top_k=top_k,
            hybrid=hybrid,
            alpha=alpha,
        )

    total = sum(len(hits) for hits in results.values())
    logger.debug(
        "get_relevant_memories user=%s agent=%s -> %d total hits across %d collections",
        user_id,
        agent_id,
        total,
        len(target_collections),
    )
    return results


# ----------------------------------------------------------------------
# Structured (SQL) canonical facts — precise lookups
# ----------------------------------------------------------------------
def get_canonical_facts(user_id: str, agent_id: str) -> Dict[str, str]:
    """Return the exact canonical facts (name, location, …) for a user+agent.

    Reads the structured SQL store — precise and always-current, complementing
    the fuzzy vector recall. Scoped strictly to ``user_id`` + ``agent_id``.
    """
    return get_canonical_store().get_all(user_id, agent_id)
