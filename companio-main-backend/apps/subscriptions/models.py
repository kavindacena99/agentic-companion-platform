from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Plan(TimeStampedModel):
    class BillingPeriod(models.TextChoices):
        FREE = 'free', 'Free'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'
        LIFETIME = 'lifetime', 'Lifetime'

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='USD')
    billing_period = models.CharField(max_length=20, choices=BillingPeriod.choices)
    daily_message_limit = models.PositiveIntegerField(null=True, blank=True)
    monthly_message_limit = models.PositiveIntegerField(null=True, blank=True)
    can_access_premium_agents = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'price', 'name']

    def __str__(self):
        return self.name


class UserSubscription(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        TRIALING = 'trialing', 'Trialing'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'
        PAST_DUE = 'past_due', 'Past due'

    class Provider(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        GOOGLE_PLAY = 'google_play', 'Google Play'
        APPLE_IAP = 'apple_iap', 'Apple IAP'
        STRIPE = 'stripe', 'Stripe'
        PAYHERE = 'payhere', 'PayHere'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='user_subscriptions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.MANUAL)
    provider_subscription_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.plan.code}'
