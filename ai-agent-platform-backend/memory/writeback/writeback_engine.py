"""Writeback engine — makes the AI learn from each conversation.

Orchestrates: summarize -> extract candidate facts -> **decide/dedup/update** ->
persist in ChromaDB. Rather than storing every candidate, each one is routed
through :func:`~memory.writeback.memory_updater.decide_write`, which skips
low-value or duplicate facts and updates canonical facts (name/location/…) in
place when they change. Depends only on the memory layer (no LLM, no Main
Backend). Provides a sync entry point plus an async wrapper for future scaling.
"""

import asyncio
import logging
from typing import Any, Dict, List

from memory.collections import CONVERSATION_MEMORY
from memory.writeback.fact_extractor import extract_facts
from memory.writeback.memory_classifier import classify_memory
from memory.writeback.memory_updater import decide_write, should_store
from memory.writeback.summarizer import summarize_conversation

logger = logging.getLogger("agent_core")


def _last_user_message(messages: List[Dict]) -> str:
    for entry in reversed(messages or []):
        if (entry.get("role") or "user").lower() == "user":
            return entry.get("content") or ""
    return ""


def process_writeback(
    user_id: str,
    agent_id: str,
    messages: List[Dict],
    response: str,
) -> List[Dict[str, Any]]:
    """Summarize, extract, and agentically persist memories for one exchange.

    Returns a record per candidate describing the decision taken
    (``insert`` / ``update`` / ``skip``) and where.
    """
    updates: List[Dict[str, Any]] = []

    # Build the candidate list: a conversation summary plus extracted facts.
    candidates: List[Dict[str, Any]] = []
    summary = summarize_conversation(messages)
    if summary:
        candidates.append(
            {"type": "summary", "content": summary, "importance": "medium", "canonical": False}
        )
    candidates.extend(extract_facts(_last_user_message(messages), response))

    # Decide store-or-skip per candidate, then dedup / update / insert.
    for fact in candidates:
        if not should_store(fact):
            updates.append(
                {"action": "skip", "reason": "low_value", "content": fact.get("content")}
            )
            continue
        collection = classify_memory(fact)
        result = decide_write(collection, user_id, agent_id, fact)
        updates.append({"collection": collection, "importance": fact.get("importance", "medium"), **result})

    stored = sum(1 for u in updates if u.get("action") in ("insert", "update"))
    logger.info(
        "Writeback for user=%s agent=%s: %d candidates -> %d stored/updated, %d skipped.",
        user_id,
        agent_id,
        len(updates),
        stored,
        len(updates) - stored,
    )
    return updates


async def aprocess_writeback(
    user_id: str,
    agent_id: str,
    messages: List[Dict],
    response: str,
) -> List[Dict[str, Any]]:
    """Async wrapper: run the (blocking) writeback in a worker thread."""
    return await asyncio.to_thread(
        process_writeback, user_id, agent_id, messages, response
    )
