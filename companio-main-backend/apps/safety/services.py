from django.db import IntegrityError
from rest_framework import exceptions

from apps.chats.models import ChatMessage

from .models import SafetyReport


def create_safety_report(user, message_id, category, description=''):
    try:
        message = ChatMessage.objects.select_related('session').get(id=message_id)
    except ChatMessage.DoesNotExist as exc:
        raise exceptions.ValidationError({'message_id': 'Message does not exist.'}) from exc

    if message.session.user_id != user.id:
        raise exceptions.PermissionDenied('You cannot report this message.')

    if message.sender != ChatMessage.Sender.AGENT:
        raise exceptions.ValidationError({'message_id': 'Only agent messages can be reported.'})

    try:
        report, created = SafetyReport.objects.get_or_create(
            reported_by=user,
            message=message,
            category=category,
            defaults={
                'session': message.session,
                'description': description,
            },
        )
    except IntegrityError as exc:
        raise exceptions.ValidationError({'message_id': 'This report already exists.'}) from exc

    if not created:
        raise exceptions.ValidationError({'message_id': 'This report already exists.'})

    return report


def get_user_reports(user):
    return SafetyReport.objects.select_related('session', 'message').filter(reported_by=user)
