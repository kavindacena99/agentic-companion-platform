import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions, status

from apps.agent_gateway.exceptions import (
    AgentPlatformUnavailable,
    AgentResponseFailed,
    InvalidAgentPlatformResponse,
)
from apps.agent_gateway.services import generate_agent_response
from apps.agents.models import Agent
from apps.agents.services import get_agent_detail_for_user, get_selected_agent
from apps.usage.services import (
    can_send_message,
    format_usage_status,
    get_usage_status,
    increment_message_usage,
)

from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class DailyMessageLimitReached(exceptions.APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Daily message limit reached.'
    default_code = 'daily_message_limit_reached'

    def __init__(self, usage):
        super().__init__(self.default_detail)
        self.usage = usage


class AgentResponseServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Agent service is temporarily unavailable. Please try again later.'
    default_code = 'agent_platform_unavailable'


def get_user_sessions(user):
    return ChatSession.objects.select_related('agent').filter(user=user).exclude(
        status=ChatSession.Status.DELETED,
    )


def get_user_session(user, session_id):
    try:
        return get_user_sessions(user).get(id=session_id)
    except ChatSession.DoesNotExist as exc:
        raise exceptions.NotFound('Chat session not found.') from exc


def archive_chat_session(user, session_id):
    session = get_user_session(user, session_id)
    if session.status == ChatSession.Status.DELETED:
        raise exceptions.ValidationError({'session': 'Chat session is already deleted.'})
    session.status = ChatSession.Status.ARCHIVED
    session.save(update_fields=['status', 'updated_at'])
    return session


def delete_chat_session(user, session_id):
    session = get_user_session(user, session_id)
    session.status = ChatSession.Status.DELETED
    session.save(update_fields=['status', 'updated_at'])
    return session


def get_session_messages(user, session_id):
    session = get_user_session(user, session_id)
    return session.messages.all()


def _get_agent_for_session(user, agent_key=None):
    if agent_key:
        try:
            agent = Agent.objects.get(key=agent_key)
        except Agent.DoesNotExist as exc:
            raise exceptions.ValidationError({'agent_key': 'Agent does not exist.'}) from exc
        if not agent.is_enabled:
            raise exceptions.ValidationError({'agent_key': 'This agent is not currently available.'})
        return agent

    selection = get_selected_agent(user)
    if not selection:
        raise exceptions.ValidationError({'agent_key': 'Select an agent before creating a chat session.'})
    return selection.agent


def create_chat_session(user, agent_key=None, title=None):
    agent = _get_agent_for_session(user, agent_key)
    session_title = title or f'Chat with {agent.display_name}'
    return ChatSession.objects.create(
        user=user,
        agent=agent,
        title=session_title,
    )


def create_user_message(session, content, status_value=ChatMessage.Status.COMPLETED):
    return ChatMessage.objects.create(
        session=session,
        sender=ChatMessage.Sender.USER,
        content=content,
        status=status_value,
        safety_status=ChatMessage.SafetyStatus.UNKNOWN,
    )


def create_agent_message(
    session,
    content,
    metadata=None,
    agent_request_id=None,
    safety_status=ChatMessage.SafetyStatus.UNKNOWN,
):
    return ChatMessage.objects.create(
        session=session,
        sender=ChatMessage.Sender.AGENT,
        content=content,
        status=ChatMessage.Status.COMPLETED,
        agent_request_id=agent_request_id or '',
        safety_status=safety_status,
        metadata=metadata or {},
    )


def _ensure_session_can_receive_message(user, session):
    if session.status != ChatSession.Status.ACTIVE:
        raise exceptions.ValidationError({'session': 'Chat session is not active.'})

    agent_data = get_agent_detail_for_user(user, session.agent_id)
    if not agent_data['is_available']:
        raise exceptions.ValidationError({'agent': 'This agent is not currently available.'})

    if not can_send_message(user):
        raise DailyMessageLimitReached(get_usage_status(user))


def send_message_to_agent(user, session_id, content):
    session = get_user_session(user, session_id)
    _ensure_session_can_receive_message(user, session)

    try:
        agent_response = generate_agent_response(user, session, content)
    except (AgentPlatformUnavailable, InvalidAgentPlatformResponse, AgentResponseFailed) as exc:
        logger.warning('Agent response failed for chat session %s.', session.id)
        raise AgentResponseServiceUnavailable() from exc

    with transaction.atomic():
        locked_session = ChatSession.objects.select_for_update().get(id=session.id)
        user_message = create_user_message(locked_session, content)
        response_metadata = dict(agent_response['metadata'])
        response_metadata['memory_updated'] = agent_response['memory_updated']
        agent_message = create_agent_message(
            locked_session,
            agent_response['reply'],
            metadata=response_metadata,
            agent_request_id=agent_response['agent_request_id'],
            safety_status=agent_response['safety_status'],
        )
        usage = increment_message_usage(user)
        locked_session.last_message_at = timezone.now()
        locked_session.save(update_fields=['last_message_at', 'updated_at'])

    return {
        'user_message': user_message,
        'agent_message': agent_message,
        'usage': format_usage_status(usage),
    }
