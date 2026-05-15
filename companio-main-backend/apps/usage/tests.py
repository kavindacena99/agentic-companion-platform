from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .services import (
    can_send_message,
    get_or_create_daily_usage,
    get_usage_status,
    increment_message_usage,
)


class UsageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='usage@example.com',
            username='usageuser',
            password='StrongPassword123',
        )

    def test_new_user_gets_zero_usage_status(self):
        status = get_usage_status(self.user)

        self.assertEqual(status['messages_used'], 0)
        self.assertEqual(status['remaining_messages'], status['message_limit'])

    def test_increment_message_usage(self):
        usage = increment_message_usage(self.user)

        self.assertEqual(usage.messages_used, 1)

    @override_settings(FREE_DAILY_MESSAGE_LIMIT=1)
    def test_user_cannot_send_when_limit_reached(self):
        usage = get_or_create_daily_usage(self.user)
        usage.message_limit = 1
        usage.messages_used = 1
        usage.save()

        self.assertFalse(can_send_message(self.user))


class UsageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='usageapi@example.com',
            username='usageapiuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)

    def test_user_can_view_usage_status(self):
        response = self.client.get(reverse('usage-me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['messages_used'], 0)
