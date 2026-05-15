from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.agents.models import Agent
from apps.common.models import TimeStampedModel


class ChatSession(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ARCHIVED = 'archived', 'Archived'
        DELETED = 'deleted', 'Deleted'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='chat_sessions')
    title = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_message_at', '-started_at']

    def __str__(self):
        return f'{self.user.email} - {self.title}'


class ChatMessage(TimeStampedModel):
    class Sender(models.TextChoices):
        USER = 'user', 'User'
        AGENT = 'agent', 'Agent'
        SYSTEM = 'system', 'System'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        BLOCKED = 'blocked', 'Blocked'

    class SafetyStatus(models.TextChoices):
        SAFE = 'safe', 'Safe'
        FLAGGED = 'flagged', 'Flagged'
        BLOCKED = 'blocked', 'Blocked'
        UNKNOWN = 'unknown', 'Unknown'

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=Sender.choices)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    agent_request_id = models.CharField(max_length=120, blank=True)
    safety_status = models.CharField(
        max_length=20,
        choices=SafetyStatus.choices,
        default=SafetyStatus.UNKNOWN,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender} message in session {self.session_id}'
