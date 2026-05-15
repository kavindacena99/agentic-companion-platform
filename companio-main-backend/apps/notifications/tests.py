from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import DeviceToken


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='notify@example.com',
            username='notifyuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)

    def test_register_token_creates_record(self):
        response = self.client.post(reverse('notification-device-token'), {
            'token': 'fcm-token-value',
            'platform': DeviceToken.Platform.ANDROID,
            'device_id': 'device-1',
            'app_version': '1.0.0',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(DeviceToken.objects.filter(token='fcm-token-value').exists())

    def test_register_same_token_updates_last_seen(self):
        DeviceToken.objects.create(user=self.user, token='fcm-token-value')

        response = self.client.post(reverse('notification-device-token'), {
            'token': 'fcm-token-value',
            'platform': DeviceToken.Platform.IOS,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(DeviceToken.objects.get(token='fcm-token-value').platform, DeviceToken.Platform.IOS)

    def test_deactivate_token_works(self):
        DeviceToken.objects.create(user=self.user, token='fcm-token-value')

        response = self.client.delete(reverse('notification-device-token'), {
            'token': 'fcm-token-value',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DeviceToken.objects.get(token='fcm-token-value').is_active)

    def test_user_can_update_preferences(self):
        response = self.client.patch(reverse('notification-preferences'), {
            'product_updates_enabled': True,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['product_updates_enabled'])
