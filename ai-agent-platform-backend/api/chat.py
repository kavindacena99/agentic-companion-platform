"""Chat API endpoint — the public entry to the agent-core AI system.

POST /chat/
    {"user_id", "agent_id", "session_id", "message"}
->  {"response", "emotion", "intent"}
"""

import logging

from pydantic import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from services.chat_service import process_chat
from services.schemas.message import ChatMessage

logger = logging.getLogger("agent_core")


class ChatView(APIView):
    """Run a single chat turn through the full reasoning pipeline."""

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            message = ChatMessage(**(request.data or {}))
        except ValidationError as exc:
            return Response(
                {"error": "Invalid request payload.", "detail": exc.errors()},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TypeError:
            return Response(
                {"error": "Request body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = process_chat(message)
        except Exception:  # noqa: BLE001 — never leak internals to the caller
            logger.exception("Chat pipeline failed for user=%s", message.user_id)
            return Response(
                {"error": "The agent is temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(result, status=status.HTTP_200_OK)
