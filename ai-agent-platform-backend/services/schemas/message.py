"""Inbound chat message schema.

The minimal contract describing a single user turn entering the agent-core.
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    user_id: str
    agent_id: str
    session_id: str
    message: str = Field(..., max_length=4000)
    # When true (and trace exposure is enabled server-side), the response
    # includes the decision trace + run metrics for debugging.
    debug: bool = False
