from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .serializers import (
    AgentAvailabilitySerializer,
    SelectAgentSerializer,
    SelectedAgentSerializer,
)
from .services import (
    get_agent_detail_for_user,
    get_available_agents_for_user,
    get_selected_agent_for_user,
    select_agent_for_user,
)


class AgentListView(APIView):
    def get(self, request):
        agents = get_available_agents_for_user(request.user)
        return Response(AgentAvailabilitySerializer(agents, many=True).data)


class AgentDetailView(APIView):
    def get(self, request, pk):
        agent = get_agent_detail_for_user(request.user, pk)
        return Response(AgentAvailabilitySerializer(agent).data)


class SelectAgentView(APIView):
    def post(self, request):
        serializer = SelectAgentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selection = select_agent_for_user(
            user=request.user,
            agent_key=serializer.validated_data['agent_key'],
        )
        response_data = {
            'agent': selection.agent_runtime_data,
            'selected_at': selection.selected_at,
        }
        create_audit_log(
            user=request.user,
            event_type='agent_selected',
            request=request,
            object_type='Agent',
            object_id=selection.agent_id,
            metadata={'agent_key': selection.agent.key},
        )
        return Response(
            SelectedAgentSerializer(response_data).data,
            status=status.HTTP_201_CREATED,
        )


class SelectedAgentView(APIView):
    def get(self, request):
        selection = get_selected_agent_for_user(request.user)
        return Response(SelectedAgentSerializer(selection).data)
