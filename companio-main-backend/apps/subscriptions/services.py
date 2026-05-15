from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import Plan, UserSubscription


def get_free_plan():
    plan = Plan.objects.filter(code='free', is_active=True).first()
    if plan:
        return plan

    return Plan(
        code='free',
        name='Free',
        price=0,
        currency='USD',
        billing_period=Plan.BillingPeriod.FREE,
        daily_message_limit=settings.FREE_DAILY_MESSAGE_LIMIT,
        can_access_premium_agents=False,
        is_active=True,
    )


def get_active_subscription(user):
    now = timezone.now()
    return (
        UserSubscription.objects.select_related('plan')
        .filter(
            user=user,
            status__in=[UserSubscription.Status.ACTIVE, UserSubscription.Status.TRIALING],
            plan__is_active=True,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        .order_by('-started_at')
        .first()
    )


def get_current_plan(user):
    subscription = get_active_subscription(user)
    if subscription:
        return subscription.plan
    return get_free_plan()


def user_has_active_premium(user):
    return bool(get_current_plan(user).can_access_premium_agents)


def get_subscription_status(user):
    subscription = get_active_subscription(user)
    plan = subscription.plan if subscription else get_free_plan()
    return {
        'plan_code': plan.code,
        'plan_name': plan.name,
        'status': subscription.status if subscription else UserSubscription.Status.ACTIVE,
        'daily_message_limit': plan.daily_message_limit,
        'monthly_message_limit': plan.monthly_message_limit,
        'can_access_premium_agents': plan.can_access_premium_agents,
        'expires_at': subscription.expires_at if subscription else None,
    }
