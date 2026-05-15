from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .services import get_feature_flags, get_public_app_config


class PublicAppConfigView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        create_audit_log(
            user=request.user,
            event_type='app_config_viewed',
            actor_type='system' if not request.user.is_authenticated else 'user',
            request=request,
        )
        return Response({
            'app': get_public_app_config(),
            'features': get_feature_flags(public_only=True),
        })
