from django.core.management.base import BaseCommand

from apps.app_config.models import AppConfig, FeatureFlag


APP_CONFIGS = [
    ('maintenance_mode', False, AppConfig.ValueType.BOOLEAN, 'Whether the app is in maintenance mode.'),
    ('minimum_android_version', '1.0.0', AppConfig.ValueType.STRING, 'Minimum supported Android app version.'),
    ('minimum_ios_version', '1.0.0', AppConfig.ValueType.STRING, 'Minimum supported iOS app version.'),
    ('latest_android_version', '1.0.0', AppConfig.ValueType.STRING, 'Latest Android app version.'),
    ('latest_ios_version', '1.0.0', AppConfig.ValueType.STRING, 'Latest iOS app version.'),
    ('support_email', 'support@companio.app', AppConfig.ValueType.STRING, 'Public support email.'),
    ('privacy_policy_url', '', AppConfig.ValueType.STRING, 'Privacy policy URL.'),
    ('terms_url', '', AppConfig.ValueType.STRING, 'Terms of service URL.'),
]

FEATURE_FLAGS = [
    ('chat_enabled', 'Chat Enabled', True, True),
    ('subscriptions_enabled', 'Subscriptions Enabled', False, True),
    ('safety_reports_enabled', 'Safety Reports Enabled', True, True),
    ('notifications_enabled', 'Notifications Enabled', True, True),
    ('premium_agents_enabled', 'Premium Agents Enabled', False, True),
]


class Command(BaseCommand):
    help = 'Create or update public Companio app configuration and feature flags.'

    def handle(self, *args, **options):
        for key, value, value_type, description in APP_CONFIGS:
            AppConfig.objects.update_or_create(
                key=key,
                defaults={
                    'value': value,
                    'value_type': value_type,
                    'description': description,
                    'is_public': True,
                    'is_active': True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f'Seeded config: {key}'))

        for key, name, is_enabled, is_public in FEATURE_FLAGS:
            FeatureFlag.objects.update_or_create(
                key=key,
                defaults={
                    'name': name,
                    'is_enabled': is_enabled,
                    'is_public': is_public,
                    'rollout_percentage': 100,
                },
            )
            self.stdout.write(self.style.SUCCESS(f'Seeded feature flag: {key}'))
