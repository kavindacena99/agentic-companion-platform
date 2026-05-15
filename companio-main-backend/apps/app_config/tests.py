from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import AppConfig, FeatureFlag
from .services import is_feature_enabled


class AppConfigTests(TestCase):
    def test_public_endpoint_only_returns_public_active_config(self):
        AppConfig.objects.create(
            key='maintenance_mode',
            value=False,
            value_type=AppConfig.ValueType.BOOLEAN,
            is_public=True,
            is_active=True,
        )
        AppConfig.objects.create(
            key='secret_internal',
            value='hidden',
            value_type=AppConfig.ValueType.STRING,
            is_public=False,
            is_active=True,
        )
        FeatureFlag.objects.create(key='chat_enabled', name='Chat Enabled', is_enabled=True, is_public=True)

        response = self.client.get(reverse('app-config-public'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('maintenance_mode', response.json()['app'])
        self.assertNotIn('secret_internal', response.json()['app'])

    def test_feature_flag_status_works(self):
        FeatureFlag.objects.create(key='chat_enabled', name='Chat Enabled', is_enabled=True)

        self.assertTrue(is_feature_enabled('chat_enabled'))

    def test_seed_app_config_is_idempotent(self):
        call_command('seed_app_config')
        call_command('seed_app_config')

        self.assertEqual(AppConfig.objects.count(), 8)
        self.assertEqual(FeatureFlag.objects.count(), 5)
