from django.conf import settings
from django.db.models import F
from django.utils import timezone

from .models import DailyUsage


def get_or_create_daily_usage(user, date=None):
    usage_date = date or timezone.localdate()
    message_limit = settings.FREE_DAILY_MESSAGE_LIMIT
    try:
        from apps.subscriptions.services import get_current_plan

        plan_limit = get_current_plan(user).daily_message_limit
        if plan_limit:
            message_limit = plan_limit
    except Exception:
        pass

    usage, _created = DailyUsage.objects.get_or_create(
        user=user,
        date=usage_date,
        defaults={'message_limit': message_limit},
    )
    if not _created and usage.message_limit != message_limit:
        usage.message_limit = message_limit
        usage.save(update_fields=['message_limit'])
    return usage


def format_usage_status(usage):
    remaining_messages = max(usage.message_limit - usage.messages_used, 0)
    return {
        'date': usage.date.isoformat(),
        'messages_used': usage.messages_used,
        'message_limit': usage.message_limit,
        'remaining_messages': remaining_messages,
        'can_send_message': remaining_messages > 0,
    }


def get_usage_status(user):
    return format_usage_status(get_or_create_daily_usage(user))


def can_send_message(user):
    usage = get_or_create_daily_usage(user)
    return usage.messages_used < usage.message_limit


def increment_message_usage(user):
    usage = get_or_create_daily_usage(user)
    DailyUsage.objects.filter(id=usage.id).update(messages_used=F('messages_used') + 1)
    usage.refresh_from_db()
    return usage
