from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.agents.models import Agent
from apps.chats.models import ChatMessage, ChatSession

from .models import SafetyReport


class SafetyReportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='safety@example.com',
            username='safetyuser',
            password='StrongPassword123',
        )
        self.other_user = get_user_model().objects.create_user(
            email='othersafety@example.com',
            username='othersafetyuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)
        self.agent = Agent.objects.create(
            key='best_friend',
            display_name='Best Friend',
            agent_type=Agent.AgentType.FRIEND,
        )
        self.session = ChatSession.objects.create(user=self.user, agent=self.agent, title='Chat')
        self.agent_message = ChatMessage.objects.create(
            session=self.session,
            sender=ChatMessage.Sender.AGENT,
            content='Agent reply',
            status=ChatMessage.Status.COMPLETED,
        )

    def test_user_can_report_own_session_agent_message(self):
        response = self.client.post(reverse('safety-report-create'), {
            'message_id': self.agent_message.id,
            'category': SafetyReport.Category.UNSAFE_RESPONSE,
            'description': 'This felt unsafe.',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], SafetyReport.Status.PENDING)

    def test_user_cannot_report_another_users_message(self):
        other_session = ChatSession.objects.create(
            user=self.other_user,
            agent=self.agent,
            title='Other chat',
        )
        other_message = ChatMessage.objects.create(
            session=other_session,
            sender=ChatMessage.Sender.AGENT,
            content='Other reply',
            status=ChatMessage.Status.COMPLETED,
        )

        response = self.client.post(reverse('safety-report-create'), {
            'message_id': other_message.id,
            'category': SafetyReport.Category.UNSAFE_RESPONSE,
        }, format='json')

        self.assertEqual(response.status_code, 403)

    def test_user_cannot_report_user_message(self):
        user_message = ChatMessage.objects.create(
            session=self.session,
            sender=ChatMessage.Sender.USER,
            content='My own message',
            status=ChatMessage.Status.COMPLETED,
        )

        response = self.client.post(reverse('safety-report-create'), {
            'message_id': user_message.id,
            'category': SafetyReport.Category.UNSAFE_RESPONSE,
        }, format='json')

        self.assertEqual(response.status_code, 400)

    def test_duplicate_report_is_rejected(self):
        SafetyReport.objects.create(
            reported_by=self.user,
            session=self.session,
            message=self.agent_message,
            category=SafetyReport.Category.UNSAFE_RESPONSE,
        )

        response = self.client.post(reverse('safety-report-create'), {
            'message_id': self.agent_message.id,
            'category': SafetyReport.Category.UNSAFE_RESPONSE,
        }, format='json')

        self.assertEqual(response.status_code, 400)
