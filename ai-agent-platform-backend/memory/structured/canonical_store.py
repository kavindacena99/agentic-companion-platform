"""SQLite-backed canonical-fact store — the structured half of memory.

Canonical facts are the *single-valued* things about a user that should have
exactly one current value: their name, where they live, their occupation. The
ChromaDB vector store is great for fuzzy semantic recall but is a poor system of
record for these — nothing stops two contradictory "location" vectors from
coexisting. This store gives them a precise home:

* **one row per** ``(user_id, agent_id, attribute)`` — a natural upsert key, so a
  changed value overwrites in place and precise lookups are O(1) and exact;
* **strict isolation** — every read and write is scoped by ``user_id`` *and*
  ``agent_id`` (they are part of the primary key);
* **Django-free** — plain stdlib :mod:`sqlite3`, matching the rest of the
  ``memory/`` engine, with its own DB file (``CANONICAL_DB_PATH``).

Vectors for fuzzy recall, this table for precise lookups — the two complement
each other; writeback keeps them in sync.
"""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger("agent_core")

DEFAULT_CANONICAL_DB_PATH = "./canonical_facts.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS canonical_facts (
    user_id    TEXT NOT NULL,
    agent_id   TEXT NOT NULL,
    attribute  TEXT NOT NULL,
    value      TEXT NOT NULL,
    importance TEXT NOT NULL DEFAULT 'medium',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, agent_id, attribute)
);
"""


class CanonicalFactStore:
    """A tiny SQL table of exact, single-valued user facts."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("CANONICAL_DB_PATH", DEFAULT_CANONICAL_DB_PATH)
        self._lock = threading.Lock()
        self._ensure_schema()

    @contextmanager
    def _connect(self):
        parent = os.path.dirname(os.path.abspath(self.path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(_SCHEMA)

    def upsert(
        self,
        user_id: str,
        agent_id: str,
        attribute: str,
        value: str,
        importance: str = "medium",
    ) -> str:
        """Insert or overwrite a canonical fact; return the action taken.

        Returns ``"inserted"`` (new attribute), ``"updated"`` (value changed —
        i.e. a contradiction resolved in place), or ``"unchanged"`` (same value).
        """
        value = (value or "").strip()
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM canonical_facts WHERE user_id=? AND agent_id=? AND attribute=?",
                (user_id, agent_id, attribute),
            ).fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO canonical_facts "
                    "(user_id, agent_id, attribute, value, importance, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, agent_id, attribute, value, importance, now),
                )
                return "inserted"

            if (row["value"] or "").strip().lower() == value.lower():
                return "unchanged"

            conn.execute(
                "UPDATE canonical_facts SET value=?, importance=?, updated_at=? "
                "WHERE user_id=? AND agent_id=? AND attribute=?",
                (value, importance, now, user_id, agent_id, attribute),
            )
            return "updated"

    def get(self, user_id: str, agent_id: str, attribute: str) -> Optional[str]:
        """Return the current value for one canonical ``attribute`` (or ``None``)."""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM canonical_facts WHERE user_id=? AND agent_id=? AND attribute=?",
                (user_id, agent_id, attribute),
            ).fetchone()
            return row["value"] if row else None

    def get_all(self, user_id: str, agent_id: str) -> Dict[str, str]:
        """Return every canonical fact for a user+agent as ``{attribute: value}``."""
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT attribute, value FROM canonical_facts "
                "WHERE user_id=? AND agent_id=? ORDER BY attribute",
                (user_id, agent_id),
            ).fetchall()
            return {row["attribute"]: row["value"] for row in rows}

    def delete(self, user_id: str, agent_id: str, attribute: str) -> int:
        """Delete a canonical fact; return the number of rows removed (0 or 1)."""
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM canonical_facts WHERE user_id=? AND agent_id=? AND attribute=?",
                (user_id, agent_id, attribute),
            )
            return cursor.rowcount


# ----------------------------------------------------------------------
# Shared default store (cached; resettable for tests / config changes)
# ----------------------------------------------------------------------
_store: Optional[CanonicalFactStore] = None


def get_canonical_store() -> CanonicalFactStore:
    """Return the process-wide canonical-fact store, building it on first use."""
    global _store
    if _store is None:
        _store = CanonicalFactStore()
        logger.info("Canonical fact store initialized at %s", _store.path)
    return _store


def reset_canonical_store() -> None:
    """Clear the cached store so the next call re-reads ``CANONICAL_DB_PATH``."""
    global _store
    _store = None
