from django.contrib import admin

from .models import Plan, UserSubscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'name',
        'price',
        'currency',
        'billing_period',
        'daily_message_limit',
        'can_access_premium_agents',
        'is_active',
        'sort_order',
    ]
    list_filter = ['billing_period', 'is_active', 'can_access_premium_agents']
    search_fields = ['code', 'name']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'provider', 'started_at', 'expires_at', 'auto_renew']
    list_filter = ['status', 'provider', 'plan']
    search_fields = ['user__email', 'provider_subscription_id', 'plan__code']
    autocomplete_fields = ['user', 'plan']
