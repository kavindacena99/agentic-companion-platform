from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'actor_type', 'object_type', 'object_id', 'created_at']
    list_filter = ['event_type', 'actor_type', 'created_at']
    search_fields = ['user__email', 'event_type', 'object_type', 'object_id']
    readonly_fields = [
        'user',
        'event_type',
        'actor_type',
        'ip_address',
        'user_agent',
        'object_type',
        'object_id',
        'metadata',
        'created_at',
    ]
