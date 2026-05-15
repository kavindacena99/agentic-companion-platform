from rest_framework import serializers

from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'code',
            'name',
            'description',
            'price',
            'currency',
            'billing_period',
            'daily_message_limit',
            'monthly_message_limit',
            'can_access_premium_agents',
        ]


class SubscriptionStatusSerializer(serializers.Serializer):
    plan_code = serializers.CharField()
    plan_name = serializers.CharField()
    status = serializers.CharField()
    daily_message_limit = serializers.IntegerField(allow_null=True)
    monthly_message_limit = serializers.IntegerField(allow_null=True)
    can_access_premium_agents = serializers.BooleanField()
    expires_at = serializers.DateTimeField(allow_null=True)
