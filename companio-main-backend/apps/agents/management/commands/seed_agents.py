from django.core.management.base import BaseCommand

from apps.agents.models import Agent


MVP_AGENTS = [
    {
        'key': 'best_friend',
        'display_name': 'Best Friend',
        'short_description': 'A supportive companion for everyday conversation and encouragement.',
        'agent_type': Agent.AgentType.FRIEND,
        'is_enabled': True,
        'is_premium': False,
        'sort_order': 10,
    },
    {
        'key': 'girlfriend',
        'display_name': 'Girlfriend',
        'short_description': 'A warm romantic companion for caring and emotionally aware chats.',
        'agent_type': Agent.AgentType.ROMANTIC,
        'is_enabled': True,
        'is_premium': False,
        'sort_order': 20,
    },
    {
        'key': 'boyfriend',
        'display_name': 'Boyfriend',
        'short_description': 'A warm romantic companion for caring and emotionally aware chats.',
        'agent_type': Agent.AgentType.ROMANTIC,
        'is_enabled': True,
        'is_premium': False,
        'sort_order': 30,
    },
]


class Command(BaseCommand):
    help = 'Create or update Companio MVP product-level agent records.'

    def handle(self, *args, **options):
        for agent_data in MVP_AGENTS:
            agent, created = Agent.objects.update_or_create(
                key=agent_data['key'],
                defaults=agent_data,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} agent: {agent.key}'))
