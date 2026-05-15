from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agent
from .serializers import (
    AgentSerializer,
    SelectAgentSerializer,
    SelectedAgentSerializer,
)
from .services import (
    get_enabled_agent_by_id,
    get_enabled_agents,
    get_selected_agent,
    select_agent_for_user,
)


class AgentListView(generics.ListAPIView):
    serializer_class = AgentSerializer

    def get_queryset(self):
        return get_enabled_agents()


class AgentDetailView(generics.RetrieveAPIView):
    serializer_class = AgentSerializer
    queryset = Agent.objects.none()

    def get_object(self):
        return get_enabled_agent_by_id(self.kwargs['pk'])


class SelectAgentView(APIView):
    def post(self, request):
        serializer = SelectAgentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selection = select_agent_for_user(
            user=request.user,
            agent_key=serializer.validated_data['agent_key'],
        )
        return Response(
            SelectedAgentSerializer(selection).data,
            status=status.HTTP_201_CREATED,
        )


class SelectedAgentView(APIView):
    def get(self, request):
        selection = get_selected_agent(request.user)
        if not selection:
            return Response({'agent': None, 'selected_at': None})

        return Response(SelectedAgentSerializer(selection).data)
