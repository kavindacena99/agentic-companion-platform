from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class DailyUsage(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_usage',
    )
    date = models.DateField()
    messages_used = models.PositiveIntegerField(default=0)
    message_limit = models.PositiveIntegerField(default=settings.FREE_DAILY_MESSAGE_LIMIT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_daily_usage_per_user_date'),
        ]
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.email} usage for {self.date}'
