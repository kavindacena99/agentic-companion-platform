"""Chat gateway endpoint.

POST /api/v1/chat/ — a secured forwarding endpoint for integration
against agent-core. It performs validation (agent is
active) and forwards the request to agent-core's /chat/ API, returning the AI
response directly.

Payment/subscription access checks are intentionally skipped here.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle

from apps.agents.models import Agent

from .agent_client import send_to_agent_core
from .exceptions import AgentPlatformUnavailable, InvalidAgentPlatformResponse

logger = logging.getLogger(__name__)


class ChatGatewayView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        agent_id = data.get('agent_id')
        message = data.get('message')

        # --- basic payload validation ---
        missing = [
            field
            for field in ('agent_id', 'message')
            if not data.get(field)
        ]
        if missing:
            return Response(
                {'error': f'Missing required field(s): {", ".join(missing)}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- STEP 1: validate agent exists and is active ---
        if not Agent.objects.filter(key=agent_id, is_enabled=True).exists():
            return Response(
                {'error': 'The requested resource was not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Access/payment checks intentionally skipped for integration testing.

        # --- STEP 2: forward to agent-core ---
        user_id = request.user.pk
        payload = {
            'user_id': str(user_id),
            'agent_id': str(agent_id),
            # agent-core requires a session_id; derive a stable one if absent.
            'session_id': str(data.get('session_id') or f'pm-{user_id}-{agent_id}'),
            'message': str(message),
        }

        try:
            agent_response = send_to_agent_core(payload)
        except (AgentPlatformUnavailable, InvalidAgentPlatformResponse):
            return Response(
                {'error': 'Agent service unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --- STEP 3: return agent-core response directly ---
        return Response(agent_response, status=status.HTTP_200_OK)
