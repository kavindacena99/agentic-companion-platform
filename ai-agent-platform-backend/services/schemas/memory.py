"""Structured memory schema for the vector store (ChromaDB).

Describes a single memory record. This is a data contract only — it does not
read from or write to any database.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class MemoryItem(BaseModel):
    id: Optional[str] = None
    user_id: str
    agent_id: str

    memory_type: str  # user / conversation / emotional / behavior

    content: str
    metadata: Dict[str, Any] = {}

    embedding_text: Optional[str] = None
