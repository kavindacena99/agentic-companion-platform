from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Plan, UserSubscription
from .services import get_subscription_status


class SubscriptionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='sub@example.com',
            username='subuser',
            password='StrongPassword123',
        )

    def test_seed_plans_creates_three_plans_idempotently(self):
        call_command('seed_plans')
        call_command('seed_plans')

        self.assertEqual(Plan.objects.count(), 3)

    def test_user_without_subscription_returns_free_status(self):
        status = get_subscription_status(self.user)

        self.assertEqual(status['plan_code'], 'free')
        self.assertFalse(status['can_access_premium_agents'])

    def test_active_premium_subscription_returns_premium_status(self):
        plan = Plan.objects.create(
            code='premium_monthly',
            name='Premium Monthly',
            price='9.99',
            currency='USD',
            billing_period=Plan.BillingPeriod.MONTHLY,
            daily_message_limit=200,
            can_access_premium_agents=True,
        )
        UserSubscription.objects.create(user=self.user, plan=plan, status=UserSubscription.Status.ACTIVE)

        status = get_subscription_status(self.user)

        self.assertEqual(status['plan_code'], 'premium_monthly')
        self.assertTrue(status['can_access_premium_agents'])

    def test_expired_subscription_falls_back_to_free(self):
        plan = Plan.objects.create(
            code='premium_yearly',
            name='Premium Yearly',
            price='99.99',
            currency='USD',
            billing_period=Plan.BillingPeriod.YEARLY,
            daily_message_limit=300,
            can_access_premium_agents=True,
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            status=UserSubscription.Status.ACTIVE,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        status = get_subscription_status(self.user)

        self.assertEqual(status['plan_code'], 'free')
