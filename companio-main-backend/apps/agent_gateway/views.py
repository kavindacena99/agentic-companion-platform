"""Chat gateway endpoint.

POST /api/v1/chat/ — a thin forwarding endpoint for manual/Postman integration
testing against agent-core. It performs light validation (user exists, agent is
active) and forwards the request to agent-core's /chat/ API, returning the AI
response directly.

Payment/subscription access checks are intentionally skipped here (this is a
testing gateway). Authentication is left open (AllowAny) so it can be exercised
from Postman without a JWT; tighten this before any production use.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents.models import Agent

from .agent_client import send_to_agent_core
from .exceptions import AgentPlatformUnavailable, InvalidAgentPlatformResponse

logger = logging.getLogger(__name__)

User = get_user_model()


class ChatGatewayView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        user_id = data.get('user_id')
        agent_id = data.get('agent_id')
        message = data.get('message')

        # --- basic payload validation ---
        missing = [
            field
            for field in ('user_id', 'agent_id', 'message')
            if not data.get(field)
        ]
        if missing:
            return Response(
                {'error': f'Missing required field(s): {", ".join(missing)}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- STEP 1: validate user exists ---
        if not User.objects.filter(pk=user_id).exists():
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- STEP 1: validate agent exists and is active ---
        if not Agent.objects.filter(key=agent_id, is_enabled=True).exists():
            return Response(
                {'error': 'Agent not found or not active.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Access/payment checks intentionally skipped for integration testing.

        # --- STEP 2: forward to agent-core ---
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
