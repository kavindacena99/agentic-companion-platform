from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Agent(TimeStampedModel):
    class AgentType(models.TextChoices):
        FRIEND = 'friend', 'Friend'
        ROMANTIC = 'romantic', 'Romantic'
        MENTOR = 'mentor', 'Mentor'
        WELLNESS = 'wellness', 'Wellness'
        PRODUCTIVITY = 'productivity', 'Productivity'

    key = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    short_description = models.CharField(max_length=500, blank=True)
    agent_type = models.CharField(max_length=30, choices=AgentType.choices)
    is_enabled = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'display_name']

    def __str__(self):
        return self.display_name


class UserAgentSelection(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agent_selections',
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name='user_selections',
    )
    selected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-selected_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['agent', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.email} selected {self.agent.key}'
