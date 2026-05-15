from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from apps.common.models import TimeStampedModel

key_validator = RegexValidator(
    regex=r'^[a-z0-9_]+$',
    message='Use lowercase letters, numbers, and underscores only.',
)


class AppConfig(TimeStampedModel):
    class ValueType(models.TextChoices):
        STRING = 'string', 'String'
        INTEGER = 'integer', 'Integer'
        BOOLEAN = 'boolean', 'Boolean'
        JSON = 'json', 'JSON'
        DECIMAL = 'decimal', 'Decimal'

    key = models.CharField(max_length=100, unique=True, validators=[key_validator])
    value = models.JSONField()
    value_type = models.CharField(max_length=20, choices=ValueType.choices, default=ValueType.STRING)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key


class FeatureFlag(TimeStampedModel):
    key = models.CharField(max_length=100, unique=True, validators=[key_validator])
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)
    rollout_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key
