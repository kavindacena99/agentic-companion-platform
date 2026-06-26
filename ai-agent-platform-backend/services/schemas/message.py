"""Inbound chat message schema.

The minimal contract describing a single user turn entering the agent-core.
"""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    user_id: str
    agent_id: str
    session_id: str
    message: str
