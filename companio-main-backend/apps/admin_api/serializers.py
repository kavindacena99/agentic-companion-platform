from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.agents.models import Agent, UserAgentSelection
from apps.app_config.models import AppConfig, FeatureFlag
from apps.chats.models import ChatMessage, ChatSession
from apps.safety.models import SafetyReport
from apps.subscriptions.models import Plan, UserSubscription
from apps.usage.models import DailyUsage

User = get_user_model()


# ── Users ──────────────────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'role',
            'is_active',
            'is_staff',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'email', 'username', 'date_joined', 'created_at', 'updated_at']


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'role', 'is_active', 'is_staff']


# ── Agents ─────────────────────────────────────────────────────────────────────

class AdminAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            'id',
            'key',
            'display_name',
            'short_description',
            'agent_type',
            'is_enabled',
            'is_premium',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']


class AdminAgentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            'key',
            'display_name',
            'short_description',
            'agent_type',
            'is_enabled',
            'is_premium',
            'sort_order',
        ]


# ── Plans ──────────────────────────────────────────────────────────────────────

class AdminPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id',
            'code',
            'name',
            'description',
            'price',
            'currency',
            'billing_period',
            'daily_message_limit',
            'monthly_message_limit',
            'can_access_premium_agents',
            'is_active',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class AdminPlanCreateSerializer(serializers.ModelSerializer):
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
            'is_active',
            'sort_order',
        ]


# ── Subscriptions ──────────────────────────────────────────────────────────────

class AdminSubscriptionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    plan_code = serializers.CharField(source='plan.code', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'user_email',
            'plan_code',
            'plan_name',
            'status',
            'provider',
            'provider_subscription_id',
            'started_at',
            'expires_at',
            'auto_renew',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'plan_code', 'plan_name', 'created_at', 'updated_at']


# ── Safety reports ─────────────────────────────────────────────────────────────

class AdminSafetyReportSerializer(serializers.ModelSerializer):
    reported_by_email = serializers.EmailField(source='reported_by.email', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)

    class Meta:
        model = SafetyReport
        fields = [
            'id',
            'reported_by_email',
            'session_id',
            'message_id',
            'category',
            'description',
            'status',
            'reviewed_by_email',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'reported_by_email',
            'session_id',
            'message_id',
            'category',
            'description',
            'created_at',
            'updated_at',
        ]


class AdminSafetyReportReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyReport
        fields = ['status']


# ── App config ─────────────────────────────────────────────────────────────────

class AdminAppConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfig
        fields = [
            'id',
            'key',
            'value',
            'value_type',
            'description',
            'is_public',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']


class AdminAppConfigCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfig
        fields = ['key', 'value', 'value_type', 'description', 'is_public', 'is_active']


# ── Feature flags ──────────────────────────────────────────────────────────────

class AdminFeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = [
            'id',
            'key',
            'name',
            'description',
            'is_enabled',
            'rollout_percentage',
            'is_public',
        ]
        read_only_fields = ['id', 'key']


class AdminFeatureFlagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ['key', 'name', 'description', 'is_enabled', 'rollout_percentage', 'is_public']


# ── Stats overview ─────────────────────────────────────────────────────────────

class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_agents = serializers.IntegerField()
    enabled_agents = serializers.IntegerField()
    total_plans = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    total_chat_sessions = serializers.IntegerField()
    total_messages_today = serializers.IntegerField()
    pending_safety_reports = serializers.IntegerField()
