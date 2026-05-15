from django.db import transaction
from django.utils import timezone

from .models import DeviceToken, NotificationPreference


@transaction.atomic
def register_device_token(user, token, platform, device_id=None, app_version=None):
    if device_id:
        DeviceToken.objects.filter(user=user, device_id=device_id).exclude(token=token).update(
            is_active=False,
        )

    device_token, _created = DeviceToken.objects.update_or_create(
        token_hash=DeviceToken.hash_token(token),
        defaults={
            'user': user,
            'token': token,
            'platform': platform,
            'device_id': device_id or '',
            'app_version': app_version or '',
            'is_active': True,
            'last_seen_at': timezone.now(),
        },
    )
    return device_token


def deactivate_device_token(user, token=None, device_id=None):
    queryset = DeviceToken.objects.filter(user=user)
    if token:
        queryset = queryset.filter(token_hash=DeviceToken.hash_token(token))
    elif device_id:
        queryset = queryset.filter(device_id=device_id)
    else:
        return 0

    return queryset.update(is_active=False)


def get_or_create_notification_preferences(user):
    preferences, _created = NotificationPreference.objects.get_or_create(user=user)
    return preferences


def update_notification_preferences(user, data):
    preferences = get_or_create_notification_preferences(user)
    for field, value in data.items():
        setattr(preferences, field, value)
    preferences.save(update_fields=list(data.keys()) + ['updated_at'])
    return preferences
