import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class DeviceToken(TimeStampedModel):
    class Platform(models.TextChoices):
        ANDROID = 'android', 'Android'
        IOS = 'ios', 'iOS'
        WEB = 'web', 'Web'
        UNKNOWN = 'unknown', 'Unknown'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField()
    token_hash = models.CharField(max_length=64, unique=True)
    platform = models.CharField(max_length=20, choices=Platform.choices, default=Platform.UNKNOWN)
    device_id = models.CharField(max_length=255, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['user', 'device_id']),
            models.Index(fields=['token_hash'], name='notificatio_token_h_b7bf74_idx'),
        ]

    def __str__(self):
        return f'{self.user.email} {self.platform} token'

    @property
    def masked_token(self):
        if len(self.token) <= 12:
            return '***'
        return f'{self.token[:6]}...{self.token[-6:]}'

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        self.token_hash = self.hash_token(self.token)
        super().save(*args, **kwargs)


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    push_enabled = models.BooleanField(default=True)
    chat_reminders_enabled = models.BooleanField(default=True)
    product_updates_enabled = models.BooleanField(default=False)
    safety_notifications_enabled = models.BooleanField(default=True)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f'Notification preferences for {self.user.email}'
