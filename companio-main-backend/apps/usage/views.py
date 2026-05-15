from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UsageStatusSerializer
from .services import get_usage_status


class CurrentUsageView(APIView):
    def get(self, request):
        serializer = UsageStatusSerializer(get_usage_status(request.user))
        return Response(serializer.data)
