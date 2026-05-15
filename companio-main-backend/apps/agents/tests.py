from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.agent_gateway.exceptions import AgentPlatformUnavailable

from .models import Agent, UserAgentSelection


def runtime_agent(
    agent_key='best_friend',
    runtime_enabled=True,
    runtime_status='active',
):
    return {
        'agent_key': agent_key,
        'display_name': 'Best Friend',
        'agent_type': 'friend',
        'runtime_enabled': runtime_enabled,
        'runtime_status': runtime_status,
        'runtime_available': runtime_enabled and runtime_status == 'active',
        'version': '1.0.0',
        'supported_features': ['chat', 'memory'],
    }


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

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_agent_list_returns_available_agents_when_runtime_is_active(self, runtime_mock):
        runtime_mock.return_value = [runtime_agent()]

        response = self.client.get(reverse('agent-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['agent_key'], 'best_friend')
        self.assertTrue(response.json()[0]['is_available'])
        self.assertEqual(response.json()[0]['availability_status'], 'available')

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_agent_list_marks_agents_unavailable_when_platform_is_down(self, runtime_mock):
        runtime_mock.side_effect = AgentPlatformUnavailable()

        response = self.client.get(reverse('agent-list'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()[0]['is_available'])
        self.assertEqual(
            response.json()[0]['availability_status'],
            'agent_platform_unavailable',
        )

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_user_can_select_agent_when_product_and_runtime_are_available(self, runtime_mock):
        runtime_mock.return_value = [runtime_agent()]

        response = self.client.post(reverse('agent-select'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['agent']['agent_key'], 'best_friend')
        self.assertTrue(
            UserAgentSelection.objects.filter(user=self.user, is_active=True).exists()
        )

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_select_fails_when_runtime_agent_is_disabled(self, runtime_mock):
        runtime_mock.return_value = [
            runtime_agent(runtime_enabled=False, runtime_status='disabled'),
        ]

        response = self.client.post(reverse('agent-select'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            UserAgentSelection.objects.filter(user=self.user, is_active=True).exists()
        )

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_select_fails_when_agent_platform_is_unavailable(self, runtime_mock):
        runtime_mock.side_effect = AgentPlatformUnavailable()

        response = self.client.post(reverse('agent-select'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()['detail'],
            'Agent service is temporarily unavailable. Please try again later.',
        )

    @patch('apps.agents.services.get_runtime_available_agents')
    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    def test_disabled_product_agent_cannot_be_selected(self, runtime_mock):
        runtime_mock.return_value = [runtime_agent()]
        self.agent.is_enabled = False
        self.agent.save(update_fields=['is_enabled'])

        response = self.client.post(reverse('agent-select'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 400)
