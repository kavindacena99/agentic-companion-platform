from django.contrib import admin

from .models import DeviceToken, NotificationPreference


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'masked_token', 'device_id', 'is_active', 'last_seen_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__email', 'device_id', 'app_version']
    readonly_fields = ['masked_token', 'last_seen_at', 'created_at', 'updated_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'push_enabled',
        'chat_reminders_enabled',
        'product_updates_enabled',
        'safety_notifications_enabled',
        'quiet_hours_enabled',
    ]
    list_filter = [
        'push_enabled',
        'chat_reminders_enabled',
        'product_updates_enabled',
        'safety_notifications_enabled',
        'quiet_hours_enabled',
    ]
    search_fields = ['user__email']
