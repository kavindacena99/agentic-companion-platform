from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class ActorType(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'
        SYSTEM = 'system', 'System'
        SERVICE = 'service', 'Service'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    event_type = models.CharField(max_length=80)
    actor_type = models.CharField(max_length=20, choices=ActorType.choices, default=ActorType.USER)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.event_type} at {self.created_at}'
