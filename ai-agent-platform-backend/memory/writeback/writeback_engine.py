"""Writeback engine — makes the AI learn from each conversation.

Orchestrates: summarize -> extract facts -> classify -> store in ChromaDB.
Depends only on the memory layer (no LLM, no Main Backend). Provides a sync
entry point plus an async wrapper for future scaling.
"""

import asyncio
import logging
from typing import Any, Dict, List

from memory.collections import CONVERSATION_MEMORY
from memory.memory_writer import store_memory
from memory.writeback.fact_extractor import extract_facts
from memory.writeback.memory_classifier import classify_memory
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
    """Summarize, extract, classify and persist memories for one exchange.

    Returns a list of writeback records describing what was stored.
    """
    updates: List[Dict[str, Any]] = []

    # 1) Conversation summary -> conversation_memory.
    summary = summarize_conversation(messages)
    if summary:
        record_id = store_memory(
            CONVERSATION_MEMORY, user_id, agent_id, summary, {"kind": "summary"}
        )
        updates.append(
            {"collection": CONVERSATION_MEMORY, "id": record_id, "content": summary}
        )

    # 2) Extract facts, classify each, and store in the right collection.
    facts = extract_facts(_last_user_message(messages), response)
    for fact in facts:
        collection = classify_memory(fact)
        record_id = store_memory(
            collection,
            user_id,
            agent_id,
            fact["content"],
            {"source_type": fact.get("type"), "importance": fact.get("importance", "medium")},
        )
        updates.append(
            {
                "collection": collection,
                "id": record_id,
                "content": fact["content"],
                "importance": fact.get("importance", "medium"),
            }
        )

    logger.info(
        "Writeback for user=%s agent=%s stored %d memories.",
        user_id,
        agent_id,
        len(updates),
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
