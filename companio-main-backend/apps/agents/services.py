from django.db import transaction
from rest_framework import exceptions

from .models import Agent, UserAgentSelection


def get_enabled_agents():
    return Agent.objects.filter(is_enabled=True).order_by('sort_order', 'display_name')


def get_enabled_agent_by_id(agent_id):
    try:
        return get_enabled_agents().get(id=agent_id)
    except Agent.DoesNotExist as exc:
        raise exceptions.NotFound('Agent not found.') from exc


def get_selected_agent(user):
    return (
        UserAgentSelection.objects.select_related('agent')
        .filter(user=user, is_active=True, agent__is_enabled=True)
        .order_by('-selected_at')
        .first()
    )


@transaction.atomic
def select_agent_for_user(user, agent_key):
    try:
        agent = Agent.objects.get(key=agent_key)
    except Agent.DoesNotExist as exc:
        raise exceptions.ValidationError({'agent_key': 'Agent does not exist.'}) from exc

    if not agent.is_enabled:
        raise exceptions.ValidationError({'agent_key': 'This agent is currently disabled.'})

    UserAgentSelection.objects.select_for_update().filter(
        user=user,
        is_active=True,
    ).update(is_active=False)

    return UserAgentSelection.objects.create(
        user=user,
        agent=agent,
        is_active=True,
    )
