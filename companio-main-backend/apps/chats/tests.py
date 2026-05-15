from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.agent_gateway.exceptions import AgentPlatformUnavailable
from apps.agents.models import Agent
from apps.chats.models import ChatMessage, ChatSession
from apps.usage.models import DailyUsage


def gateway_response():
    return {
        'reply': 'This is a temporary Companio agent response for development.',
        'agent_request_id': 'mock_req_test',
        'safety_status': 'safe',
        'memory_updated': False,
        'metadata': {'mock': True},
    }


class ChatApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='chat@example.com',
            username='chatuser',
            password='StrongPassword123',
        )
        self.other_user = get_user_model().objects.create_user(
            email='otherchat@example.com',
            username='otherchatuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            key='best_friend',
            display_name='Best Friend',
            short_description='Supportive everyday companion.',
            agent_type=Agent.AgentType.FRIEND,
            is_enabled=True,
        )

    def test_user_can_create_chat_session(self):
        response = self.client.post(reverse('chat-session-list'), {
            'agent_key': 'best_friend',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['agent_key'], 'best_friend')

    def test_user_cannot_access_another_users_session(self):
        session = ChatSession.objects.create(
            user=self.other_user,
            agent=self.agent,
            title='Private chat',
        )

        response = self.client.get(reverse('chat-session-detail', args=[session.id]))

        self.assertEqual(response.status_code, 404)

    def test_messages_are_returned_in_chronological_order(self):
        session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')
        ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.USER,
            content='First',
            status=ChatMessage.Status.COMPLETED,
        )
        ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.AGENT,
            content='Second',
            status=ChatMessage.Status.COMPLETED,
        )

        response = self.client.get(reverse('chat-session-messages', args=[session.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['content'] for item in response.json()], ['First', 'Second'])

    @override_settings(AGENT_PLATFORM_USE_MOCK=True)
    @patch('apps.chats.services.generate_agent_response')
    def test_send_message_succeeds_and_increments_usage(self, response_mock):
        response_mock.return_value = gateway_response()
        session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')

        response = self.client.post(reverse('chat-session-messages', args=[session.id]), {
            'content': 'I feel tired today',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['usage']['messages_used'], 1)
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 2)

    @override_settings(AGENT_PLATFORM_USE_MOCK=True, FREE_DAILY_MESSAGE_LIMIT=1)
    def test_send_message_does_not_increment_when_limit_reached(self):
        session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')
        DailyUsage.objects.create(
            user=self.user,
            date='2026-05-15',
            messages_used=1,
            message_limit=1,
        )

        response = self.client.post(reverse('chat-session-messages', args=[session.id]), {
            'content': 'Hello',
        }, format='json')

        self.assertEqual(response.status_code, 429)

    @override_settings(AGENT_PLATFORM_USE_MOCK=True)
    @patch('apps.chats.services.generate_agent_response')
    def test_agent_platform_failure_returns_503(self, response_mock):
        response_mock.side_effect = AgentPlatformUnavailable()
        session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')

        response = self.client.post(reverse('chat-session-messages', args=[session.id]), {
            'content': 'Hello',
        }, format='json')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 0)

    @override_settings(AGENT_PLATFORM_USE_MOCK=False)
    @patch('apps.agents.services.get_runtime_available_agents')
    def test_user_cannot_send_when_session_agent_unavailable(self, runtime_mock):
        runtime_mock.return_value = []
        session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')

        response = self.client.post(reverse('chat-session-messages', args=[session.id]), {
            'content': 'Hello',
        }, format='json')

        self.assertEqual(response.status_code, 400)
