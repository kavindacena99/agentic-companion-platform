"""Agentic memory decision layer — decide / deduplicate / update.

Replaces "store every extracted fact" with a policy that keeps user memory
clean. For each candidate fact it decides one of:

* **skip**   — too low-value to keep, or a near-duplicate already exists;
* **update** — a *canonical* fact (name / location / occupation) already exists
  for this attribute but the value changed → overwrite it in place (resolves
  contradictions like "I moved to Kandy" without adding a duplicate);
* **insert** — genuinely new information → store it.

Every read and write is strictly scoped to ``user_id`` **and** ``agent_id`` so
memory never leaks or updates across users or agents. Deterministic and
LLM-free, so writeback stays cheap, reliable, and testable.
"""

import logging
from typing import Any, Dict, List, Optional

from memory.collections import get_collection
from memory.memory_retriever import search_memory
from memory.memory_writer import store_memory, update_memory
from memory.structured.canonical_store import get_canonical_store

logger = logging.getLogger("agent_core")

# A stored memory is treated as a near-duplicate of a candidate when their
# normalized relevance (from the hybrid retriever) meets this bar.
DEDUP_RELEVANCE_THRESHOLD = 0.9

# Importance ordering + the minimum a fact needs to be worth storing. Facts
# below the floor (e.g. low-importance "User has a ...") are skipped to curb
# memory bloat. Tunable per call.
_IMPORTANCE_RANK = {"low": 0, "medium": 1, "high": 2}
DEFAULT_IMPORTANCE_FLOOR = "medium"


def should_store(fact: Dict[str, Any], floor: str = DEFAULT_IMPORTANCE_FLOOR) -> bool:
    """Whether ``fact`` clears the importance floor (bloat control)."""
    if not (fact.get("content") or "").strip():
        return False
    importance = (fact.get("importance") or "medium").lower()
    return _IMPORTANCE_RANK.get(importance, 1) >= _IMPORTANCE_RANK.get(floor, 1)


def _scoped_where(
    user_id: str, agent_id: str, extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build a Chroma ``where`` filter with mandatory user+agent scoping."""
    conditions: List[Dict[str, Any]] = [{"user_id": user_id}, {"agent_id": agent_id}]
    if extra:
        conditions.extend({key: value} for key, value in extra.items())
    return {"$and": conditions}


def _find_by_attribute(
    collection_name: str, user_id: str, agent_id: str, attribute: str
) -> List[Dict[str, Any]]:
    """Return existing records for a canonical ``attribute`` (scoped)."""
    collection = get_collection(collection_name)
    if collection.count() == 0:
        return []
    got = collection.get(where=_scoped_where(user_id, agent_id, {"attribute": attribute}))
    ids = got.get("ids") or []
    documents = got.get("documents") or []
    return [
        {"id": ids[i], "content": documents[i] if i < len(documents) else None}
        for i in range(len(ids))
    ]


def decide_write(
    collection_name: str,
    user_id: str,
    agent_id: str,
    fact: Dict[str, Any],
    dedup_threshold: float = DEDUP_RELEVANCE_THRESHOLD,
) -> Dict[str, Any]:
    """Decide and perform the write for one ``fact``; return a result record.

    Result is ``{action, id, content, reason?}`` where ``action`` is one of
    ``insert`` / ``update`` / ``skip``. All lookups and writes are scoped to
    ``user_id`` + ``agent_id``.
    """
    content = fact["content"]
    attribute = fact.get("attribute")
    canonical = bool(fact.get("canonical"))
    base_metadata = {
        "source_type": fact.get("type"),
        "importance": fact.get("importance", "medium"),
    }
    if attribute:
        base_metadata["attribute"] = attribute

    # 1) Canonical facts: the structured SQL store is the source of truth for
    # the single current value per attribute. It decides insert/update/skip; the
    # ChromaDB record is kept in sync so semantic recall still finds the fact.
    if canonical and attribute:
        importance = fact.get("importance", "medium")
        action = get_canonical_store().upsert(user_id, agent_id, attribute, content, importance)
        existing = _find_by_attribute(collection_name, user_id, agent_id, attribute)

        if action == "unchanged":
            logger.debug("Writeback skip (canonical duplicate): %s", content)
            existing_id = existing[0]["id"] if existing else None
            return {"action": "skip", "id": existing_id, "content": content, "reason": "duplicate"}

        if existing:
            update_memory(collection_name, existing[0]["id"], content, base_metadata)
            logger.info("Writeback update (%s -> %r) synced to vector store", attribute, content)
            return {"action": "update", "id": existing[0]["id"], "content": content, "reason": "contradiction"}
        # SQL says inserted/updated but no vector record yet → fall through and
        # insert one (with the attribute) so recall stays in sync.

    # 2) Deduplicate against similar existing memories (scoped similarity).
    else:
        hits = search_memory(collection_name, content, user_id, agent_id, top_k=3)
        for hit in hits:
            if float(hit.get("relevance") or 0.0) >= dedup_threshold:
                logger.debug("Writeback skip (near-duplicate rel=%.3f): %s", hit["relevance"], content)
                return {"action": "skip", "id": hit["id"], "content": content, "reason": "similar"}

    # 3) Genuinely new information → insert.
    record_id = store_memory(collection_name, user_id, agent_id, content, base_metadata)
    return {"action": "insert", "id": record_id, "content": content}
