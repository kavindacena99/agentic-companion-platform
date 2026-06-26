"""ChromaDB persistent client initialization.

Provides a single, lazily-created persistent client for the whole process.
The storage path comes from the ``CHROMA_DB_PATH`` environment variable.

This module is the only place that knows how to construct the Chroma client;
everything else goes through :func:`get_client`.
"""

import logging
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings

logger = logging.getLogger("agent_core")

_client: "chromadb.api.ClientAPI | None" = None


def get_chroma_path() -> str:
    """Return the configured persistent storage path for ChromaDB."""
    return os.getenv("CHROMA_DB_PATH", "./chroma_db")


def get_client() -> "chromadb.api.ClientAPI":
    """Return the shared persistent ChromaDB client, creating it on first use."""
    global _client
    if _client is None:
        path = get_chroma_path()
        Path(path).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB persistent client initialized at %s", path)
    return _client
