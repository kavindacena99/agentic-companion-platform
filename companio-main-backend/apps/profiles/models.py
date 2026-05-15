from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    display_name = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=30,
        choices=Gender.choices,
        blank=True,
    )
    country = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=20, default='en')
    timezone = models.CharField(max_length=100, default='Asia/Colombo')
    profile_completed = models.BooleanField(default=False)
    memory_enabled = models.BooleanField(default=True)
    personalization_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__email']

    def __str__(self):
        return f'Profile for {self.user.email}'
