from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.subscriptions.models import Plan


PLANS = [
    {
        'code': 'free',
        'name': 'Free',
        'description': 'Starter access for Companio.',
        'price': Decimal('0.00'),
        'currency': 'USD',
        'billing_period': Plan.BillingPeriod.FREE,
        'daily_message_limit': 20,
        'monthly_message_limit': None,
        'can_access_premium_agents': False,
        'is_active': True,
        'sort_order': 10,
    },
    {
        'code': 'premium_monthly',
        'name': 'Premium Monthly',
        'description': 'Monthly premium access for Companio.',
        'price': Decimal('9.99'),
        'currency': 'USD',
        'billing_period': Plan.BillingPeriod.MONTHLY,
        'daily_message_limit': 200,
        'monthly_message_limit': None,
        'can_access_premium_agents': True,
        'is_active': True,
        'sort_order': 20,
    },
    {
        'code': 'premium_yearly',
        'name': 'Premium Yearly',
        'description': 'Yearly premium access for Companio.',
        'price': Decimal('99.99'),
        'currency': 'USD',
        'billing_period': Plan.BillingPeriod.YEARLY,
        'daily_message_limit': 300,
        'monthly_message_limit': None,
        'can_access_premium_agents': True,
        'is_active': True,
        'sort_order': 30,
    },
]


class Command(BaseCommand):
    help = 'Create or update Companio subscription plans.'

    def handle(self, *args, **options):
        for plan_data in PLANS:
            plan, created = Plan.objects.update_or_create(
                code=plan_data['code'],
                defaults=plan_data,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} plan: {plan.code}'))
