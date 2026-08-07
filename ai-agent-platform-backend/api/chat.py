"""Chat API endpoint — the public entry to the agent-core AI system.

POST /chat/
    {"user_id", "agent_id", "session_id", "message"}
->  {"response", "emotion", "intent"}
"""

import logging

from django.conf import settings
from pydantic import ValidationError
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from services.chat_service import process_chat
from services.schemas.message import ChatMessage

logger = logging.getLogger("agent_core")


class HasValidServiceKey(BasePermission):
    """Require a valid X-Service-Key header for service-to-service calls."""
    def has_permission(self, request, view):
        expected = settings.AGENT_CORE_SERVICE_KEY
        if not expected:
            # Misconfigured — deny by default.
            logger.error("AGENT_CORE_SERVICE_KEY is not configured; denying request.")
            return False
        provided = request.META.get("HTTP_X_SERVICE_KEY", "")
        return provided == expected


class ChatView(APIView):
    """Run a single chat turn through the full reasoning pipeline."""

    permission_classes = [HasValidServiceKey]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

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
