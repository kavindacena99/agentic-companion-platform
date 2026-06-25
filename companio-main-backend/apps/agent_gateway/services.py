import json
import logging
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings

from .exceptions import (
    AgentPlatformUnavailable,
    AgentResponseFailed,
    InvalidAgentPlatformResponse,
)

logger = logging.getLogger(__name__)

ACTIVE_RUNTIME_STATUS = 'active'


def _build_available_agents_url():
    return urljoin(
        settings.AGENT_PLATFORM_BASE_URL.rstrip('/') + '/',
        'internal/agents/available/',
    )


def _build_chat_response_url():
    return urljoin(
        settings.AGENT_PLATFORM_BASE_URL.rstrip('/') + '/',
        'internal/chat/respond/',
    )


def _request_json(url, method='GET', payload=None):
    body = None
    headers = {
        'Accept': 'application/json',
        'X-Service-Key': settings.AGENT_PLATFORM_SERVICE_KEY,
    }
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=settings.AGENT_PLATFORM_TIMEOUT_SECONDS) as response:
            return response.read().decode('utf-8')
    except HTTPError as exc:
        logger.warning('Agent Platform returned HTTP error %s.', exc.code)
        raise AgentPlatformUnavailable('Agent Platform is unavailable.') from exc
    except URLError as exc:
        logger.warning('Agent Platform connection failed.')
        raise AgentPlatformUnavailable('Agent Platform is unavailable.') from exc
    except TimeoutError as exc:
        logger.warning('Agent Platform request timed out.')
        raise AgentPlatformUnavailable('Agent Platform is unavailable.') from exc


def _validate_runtime_agent(raw_agent):
    required_fields = ['agent_key', 'display_name', 'agent_type', 'is_enabled', 'runtime_status']
    if not isinstance(raw_agent, dict):
        raise InvalidAgentPlatformResponse('Agent Platform returned a non-object agent item.')

    missing_fields = [field for field in required_fields if field not in raw_agent]
    if missing_fields:
        raise InvalidAgentPlatformResponse('Agent Platform response is missing required fields.')

    supported_features = raw_agent.get('supported_features', [])
    if not isinstance(supported_features, list):
        raise InvalidAgentPlatformResponse('Agent Platform supported_features must be a list.')

    return {
        'agent_key': str(raw_agent['agent_key']),
        'display_name': str(raw_agent['display_name']),
        'agent_type': str(raw_agent['agent_type']),
        'runtime_enabled': bool(raw_agent['is_enabled']),
        'runtime_status': str(raw_agent['runtime_status']),
        'runtime_available': (
            bool(raw_agent['is_enabled'])
            and str(raw_agent['runtime_status']) == ACTIVE_RUNTIME_STATUS
        ),
        'version': raw_agent.get('version'),
        'supported_features': supported_features,
    }


def get_runtime_available_agents():
    body = _request_json(_build_available_agents_url())

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning('Agent Platform returned invalid JSON.')
        raise InvalidAgentPlatformResponse('Agent Platform returned invalid JSON.') from exc

    if not isinstance(payload, list):
        logger.warning('Agent Platform returned an invalid payload shape.')
        raise InvalidAgentPlatformResponse('Agent Platform response must be a list.')

    return [_validate_runtime_agent(agent) for agent in payload]


_MOCK_REPLIES = [
    "Hey! That's really interesting — tell me more about it!",
    "I'm here for you. What's on your mind?",
    "That sounds like a lot to handle. How are you feeling about it?",
    "I totally get that! I'd probably feel the same way.",
    "You always have the most thoughtful things to say. I love that about you.",
    "Honestly, that makes a lot of sense. What do you think you'll do next?",
    "I've been thinking about you! How's everything going?",
    "That's such a great point. I hadn't thought about it that way before.",
    "You're doing amazing, you know that? Keep going!",
    "Tell me everything — I'm all yours right now.",
]


def _mock_agent_response():
    import random
    return {
        'reply': random.choice(_MOCK_REPLIES),
        'agent_request_id': f'mock_req_{uuid.uuid4().hex[:12]}',
        'safety_status': 'safe',
        'memory_updated': False,
        'metadata': {
            'mock': True,
        },
    }


def _validate_agent_response(payload):
    if not isinstance(payload, dict):
        raise InvalidAgentPlatformResponse('Agent Platform response must be an object.')

    required_fields = ['reply', 'agent_request_id', 'safety_status', 'metadata']
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise InvalidAgentPlatformResponse('Agent Platform response is missing required fields.')

    if not isinstance(payload['metadata'], dict):
        raise InvalidAgentPlatformResponse('Agent Platform metadata must be an object.')

    return {
        'reply': str(payload['reply']),
        'agent_request_id': str(payload['agent_request_id']),
        'safety_status': str(payload['safety_status']),
        'memory_updated': bool(payload.get('memory_updated', False)),
        'metadata': payload['metadata'],
    }


def generate_agent_response(user, session, message_content):
    if settings.AGENT_PLATFORM_USE_MOCK:
        return _mock_agent_response()

    profile = getattr(user, 'profile', None)
    request_payload = {
        'user_id': str(user.id),
        'session_id': str(session.id),
        'agent_key': session.agent.key,
        'message': message_content,
        'metadata': {
            'language': getattr(profile, 'preferred_language', 'en'),
            'timezone': getattr(profile, 'timezone', settings.TIME_ZONE),
        },
    }

    try:
        body = _request_json(
            _build_chat_response_url(),
            method='POST',
            payload=request_payload,
        )
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning('Agent Platform returned invalid chat response JSON.')
        raise InvalidAgentPlatformResponse('Agent Platform returned invalid JSON.') from exc
    except AgentPlatformUnavailable:
        raise
    except Exception as exc:
        logger.warning('Agent Platform response generation failed.')
        raise AgentResponseFailed('Agent response generation failed.') from exc

    return _validate_agent_response(payload)
