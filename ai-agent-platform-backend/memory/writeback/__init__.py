"""Memory writeback system — the AI's automatic learning loop."""

from memory.writeback.fact_extractor import extract_facts
from memory.writeback.memory_classifier import classify_memory
from memory.writeback.summarizer import summarize_conversation
from memory.writeback.writeback_engine import aprocess_writeback, process_writeback

__all__ = [
    "summarize_conversation",
    "extract_facts",
    "classify_memory",
    "process_writeback",
    "aprocess_writeback",
]
