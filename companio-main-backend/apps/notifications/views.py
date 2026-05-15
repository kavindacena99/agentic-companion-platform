from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .serializers import (
    DeviceTokenDeactivateSerializer,
    DeviceTokenRegisterSerializer,
    NotificationPreferenceSerializer,
)
from .services import (
    deactivate_device_token,
    get_or_create_notification_preferences,
    register_device_token,
    update_notification_preferences,
)


class DeviceTokenView(APIView):
    def post(self, request):
        serializer = DeviceTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_token = register_device_token(user=request.user, **serializer.validated_data)
        create_audit_log(
            user=request.user,
            event_type='device_token_registered',
            request=request,
            object_type='DeviceToken',
            object_id=device_token.id,
            metadata={'platform': device_token.platform},
        )
        return Response({'detail': 'Device token registered successfully.'})

    def delete(self, request):
        serializer = DeviceTokenDeactivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deactivate_device_token(user=request.user, **serializer.validated_data)
        return Response({'detail': 'Device token deactivated successfully.'})


class NotificationPreferenceView(APIView):
    def get(self, request):
        preferences = get_or_create_notification_preferences(request.user)
        return Response(NotificationPreferenceSerializer(preferences).data)

    def patch(self, request):
        serializer = NotificationPreferenceSerializer(
            get_or_create_notification_preferences(request.user),
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        preferences = update_notification_preferences(request.user, serializer.validated_data)
        create_audit_log(
            user=request.user,
            event_type='notification_preferences_updated',
            request=request,
            object_type='NotificationPreference',
            object_id=preferences.id,
            metadata={'updated_fields': list(serializer.validated_data.keys())},
        )
        return Response(NotificationPreferenceSerializer(preferences).data)
