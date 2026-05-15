import logging

from .models import AuditLog

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def create_audit_log(
    user=None,
    event_type=None,
    actor_type=AuditLog.ActorType.USER,
    request=None,
    object_type=None,
    object_id=None,
    metadata=None,
):
    try:
        if not event_type:
            return None

        ip_address = _get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        safe_metadata = metadata if isinstance(metadata, dict) else {'value': str(metadata)}

        return AuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', True) else None,
            event_type=event_type,
            actor_type=actor_type,
            ip_address=ip_address or None,
            user_agent=user_agent,
            object_type=object_type or '',
            object_id=str(object_id or ''),
            metadata=safe_metadata,
        )
    except Exception:
        logger.warning('Audit log creation failed.', exc_info=True)
        return None
