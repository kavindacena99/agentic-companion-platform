"""REST API views for the agent-core service.

For the bootstrap step this only exposes a health-check endpoint used for
Postman/uptime testing. Chat and debug endpoints are added in later steps.
"""

import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("agent_core")


class HealthView(APIView):
    """Simple liveness probe for the agent-core service."""

    permission_classes = [AllowAny]

    def get(self, request):
        logger.debug("Health check requested")
        return Response({"status": "ok", "service": "agent-core"})
