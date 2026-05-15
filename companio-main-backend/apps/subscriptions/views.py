from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .models import Plan
from .serializers import PlanSerializer, SubscriptionStatusSerializer
from .services import get_subscription_status


class PlanListView(APIView):
    def get(self, request):
        plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price')
        return Response(PlanSerializer(plans, many=True).data)


class CurrentSubscriptionView(APIView):
    def get(self, request):
        status_data = get_subscription_status(request.user)
        create_audit_log(
            user=request.user,
            event_type='subscription_status_viewed',
            request=request,
            metadata={'plan_code': status_data['plan_code']},
        )
        return Response(SubscriptionStatusSerializer(status_data).data)
