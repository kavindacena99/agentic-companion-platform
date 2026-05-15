from rest_framework import serializers

from .models import DeviceToken, NotificationPreference


class DeviceTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=4096, trim_whitespace=True)
    platform = serializers.ChoiceField(choices=DeviceToken.Platform.choices)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True)


class DeviceTokenDeactivateSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=4096, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get('token') and not attrs.get('device_id'):
            raise serializers.ValidationError('Provide token or device_id.')
        return attrs


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'push_enabled',
            'chat_reminders_enabled',
            'product_updates_enabled',
            'safety_notifications_enabled',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
        ]
