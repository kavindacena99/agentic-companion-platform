from django.conf import settings
from django.db import models

from apps.chats.models import ChatMessage, ChatSession
from apps.common.models import TimeStampedModel


class SafetyReport(TimeStampedModel):
    class Category(models.TextChoices):
        UNSAFE_RESPONSE = 'unsafe_response', 'Unsafe response'
        HARMFUL_ADVICE = 'harmful_advice', 'Harmful advice'
        EMOTIONAL_MANIPULATION = 'emotional_manipulation', 'Emotional manipulation'
        DEPENDENCY_CONCERN = 'dependency_concern', 'Dependency concern'
        SEXUAL_CONTENT = 'sexual_content', 'Sexual content'
        HARASSMENT = 'harassment', 'Harassment'
        PRIVACY_CONCERN = 'privacy_concern', 'Privacy concern'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under review'
        RESOLVED = 'resolved', 'Resolved'
        DISMISSED = 'dismissed', 'Dismissed'

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='safety_reports',
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='safety_reports')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='safety_reports')
    category = models.CharField(max_length=40, choices=Category.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_safety_reports',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reported_by', 'message', 'category'],
                name='unique_safety_report_per_user_message_category',
            ),
        ]

    def __str__(self):
        return f'{self.category} report by {self.reported_by.email}'
