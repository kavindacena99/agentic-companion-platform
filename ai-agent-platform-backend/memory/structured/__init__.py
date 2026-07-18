"""Structured (SQL) memory — precise, single-valued canonical facts.

Complements the ChromaDB vector store: vectors give fuzzy semantic recall, this
table gives exact, always-current lookups for canonical facts (name, location,
occupation). See :mod:`memory.structured.canonical_store`.
"""

from memory.structured.canonical_store import (
    CanonicalFactStore,
    get_canonical_store,
    reset_canonical_store,
)

__all__ = ["CanonicalFactStore", "get_canonical_store", "reset_canonical_store"]
