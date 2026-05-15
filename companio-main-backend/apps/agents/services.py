import logging

from django.conf import settings
from django.db import transaction
from rest_framework import exceptions, status

from apps.agent_gateway.exceptions import (
    AgentPlatformUnavailable,
    InvalidAgentPlatformResponse,
)
from apps.agent_gateway.services import get_runtime_available_agents

from .models import Agent, UserAgentSelection

logger = logging.getLogger(__name__)

AVAILABLE = 'available'
PRODUCT_DISABLED = 'product_disabled'
RUNTIME_DISABLED = 'runtime_disabled'
RUNTIME_MAINTENANCE = 'runtime_maintenance'
RUNTIME_ERROR = 'runtime_error'
AGENT_PLATFORM_UNAVAILABLE = 'agent_platform_unavailable'
PREMIUM_REQUIRED = 'premium_required'

RUNTIME_STATUS_TO_AVAILABILITY = {
    'disabled': RUNTIME_DISABLED,
    'maintenance': RUNTIME_MAINTENANCE,
    'error': RUNTIME_ERROR,
}


class AgentServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Agent service is temporarily unavailable. Please try again later.'
    default_code = 'agent_platform_unavailable'


def get_product_agents():
    return Agent.objects.order_by('sort_order', 'display_name')


def get_visible_product_agents():
    # is_enabled is product-side visibility/selectability, not runtime readiness.
    return get_product_agents().filter(is_enabled=True)


def _runtime_map():
    if settings.AGENT_PLATFORM_USE_MOCK:
        return {
            agent.key: {
                'agent_key': agent.key,
                'display_name': agent.display_name,
                'agent_type': agent.agent_type,
                'runtime_enabled': True,
                'runtime_status': 'active',
                'runtime_available': True,
                'version': 'mock',
                'supported_features': ['chat'],
            }
            for agent in get_visible_product_agents()
        }

    runtime_agents = get_runtime_available_agents()
    return {agent['agent_key']: agent for agent in runtime_agents}


def _fallback_agent_data(agent):
    return {
        'id': agent.id,
        'agent_key': agent.key,
        'display_name': agent.display_name,
        'short_description': agent.short_description,
        'agent_type': agent.agent_type,
        'is_available': False,
        'availability_status': AGENT_PLATFORM_UNAVAILABLE,
        'requires_premium': agent.is_premium,
        'runtime_status': None,
        'version': None,
        'supported_features': [],
    }


def _availability_from_runtime(runtime_agent):
    if not runtime_agent:
        return False, RUNTIME_DISABLED

    runtime_status = runtime_agent['runtime_status']
    if runtime_agent['runtime_available']:
        return True, AVAILABLE

    return False, RUNTIME_STATUS_TO_AVAILABILITY.get(runtime_status, RUNTIME_ERROR)


def build_agent_response(agent, runtime_agent=None, platform_unavailable=False):
    if platform_unavailable:
        return _fallback_agent_data(agent)

    if not agent.is_enabled:
        is_available = False
        availability_status = PRODUCT_DISABLED
    else:
        is_available, availability_status = _availability_from_runtime(runtime_agent)

    return {
        'id': agent.id,
        'agent_key': agent.key,
        'display_name': agent.display_name,
        'short_description': agent.short_description,
        'agent_type': agent.agent_type,
        'is_available': is_available,
        'availability_status': availability_status,
        'requires_premium': agent.is_premium,
        'runtime_status': runtime_agent['runtime_status'] if runtime_agent else None,
        'version': runtime_agent['version'] if runtime_agent else None,
        'supported_features': runtime_agent['supported_features'] if runtime_agent else [],
    }


def get_available_agents_for_user(user):
    product_agents = list(get_visible_product_agents())

    try:
        runtime_agents_by_key = _runtime_map()
    except (AgentPlatformUnavailable, InvalidAgentPlatformResponse):
        logger.warning('Agent Platform unavailable while listing agents.')
        return [_fallback_agent_data(agent) for agent in product_agents]

    return [
        build_agent_response(agent, runtime_agents_by_key.get(agent.key))
        for agent in product_agents
    ]


def get_agent_detail_for_user(user, agent_id):
    try:
        agent = get_visible_product_agents().get(id=agent_id)
    except Agent.DoesNotExist as exc:
        raise exceptions.NotFound('Agent not found.') from exc

    try:
        runtime_agents_by_key = _runtime_map()
    except (AgentPlatformUnavailable, InvalidAgentPlatformResponse):
        logger.warning('Agent Platform unavailable while retrieving agent detail.')
        return _fallback_agent_data(agent)

    return build_agent_response(agent, runtime_agents_by_key.get(agent.key))


def get_selected_agent(user):
    return (
        UserAgentSelection.objects.select_related('agent')
        .filter(user=user, is_active=True)
        .order_by('-selected_at')
        .first()
    )


def get_selected_agent_for_user(user):
    selection = get_selected_agent(user)
    if not selection:
        return {'agent': None, 'selected_at': None}

    try:
        runtime_agents_by_key = _runtime_map()
    except (AgentPlatformUnavailable, InvalidAgentPlatformResponse):
        logger.warning('Agent Platform unavailable while checking selected agent.')
        agent_data = _fallback_agent_data(selection.agent)
    else:
        agent_data = build_agent_response(
            selection.agent,
            runtime_agents_by_key.get(selection.agent.key),
        )

    return {
        'agent': agent_data,
        'selected_at': selection.selected_at,
    }


@transaction.atomic
def select_agent_for_user(user, agent_key):
    try:
        agent = Agent.objects.get(key=agent_key)
    except Agent.DoesNotExist as exc:
        raise exceptions.ValidationError({'agent_key': 'Agent does not exist.'}) from exc

    if not agent.is_enabled:
        logger.info('Agent selection denied because product agent is disabled.')
        raise exceptions.ValidationError({'agent_key': 'This agent is not currently available.'})

    try:
        runtime_agents_by_key = _runtime_map()
    except (AgentPlatformUnavailable, InvalidAgentPlatformResponse) as exc:
        logger.warning('Agent selection denied because Agent Platform is unavailable.')
        raise AgentServiceUnavailable() from exc

    runtime_agent = runtime_agents_by_key.get(agent.key)
    is_available, _availability_status = _availability_from_runtime(runtime_agent)
    if not is_available:
        logger.info('Agent selection denied because runtime agent is unavailable.')
        raise exceptions.ValidationError({'agent_key': 'This agent is not currently available.'})

    UserAgentSelection.objects.select_for_update().filter(
        user=user,
        is_active=True,
    ).update(is_active=False)

    selection = UserAgentSelection.objects.create(
        user=user,
        agent=agent,
        is_active=True,
    )
    selection.agent_runtime_data = build_agent_response(agent, runtime_agent)
    return selection
