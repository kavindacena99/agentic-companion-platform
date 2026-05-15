from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Agent, UserAgentSelection


class AgentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='agent@example.com',
            username='agentuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            key='best_friend',
            display_name='Best Friend',
            short_description='Supportive everyday companion.',
            agent_type=Agent.AgentType.FRIEND,
            is_enabled=True,
            sort_order=10,
        )

    def test_user_can_list_enabled_agents(self):
        Agent.objects.create(
            key='disabled',
            display_name='Disabled',
            agent_type=Agent.AgentType.FRIEND,
            is_enabled=False,
        )

        response = self.client.get(reverse('agent-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['key'], 'best_friend')

    def test_user_can_select_agent(self):
        response = self.client.post(reverse('agent-select'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['agent']['key'], 'best_friend')
        self.assertTrue(
            UserAgentSelection.objects.filter(user=self.user, is_active=True).exists()
        )
