from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agents.models import Agent, UserAgentSelection
from apps.app_config.models import AppConfig, FeatureFlag
from apps.audit_logs.services import create_audit_log
from apps.chats.models import ChatSession
from apps.safety.models import SafetyReport
from apps.subscriptions.models import Plan, UserSubscription
from apps.usage.models import DailyUsage

from .permissions import IsAdminRole
from .serializers import (
    AdminAgentCreateSerializer,
    AdminAgentSerializer,
    AdminAppConfigCreateSerializer,
    AdminAppConfigSerializer,
    AdminFeatureFlagCreateSerializer,
    AdminFeatureFlagSerializer,
    AdminPlanCreateSerializer,
    AdminPlanSerializer,
    AdminSafetyReportReviewSerializer,
    AdminSafetyReportSerializer,
    AdminStatsSerializer,
    AdminSubscriptionSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)

User = get_user_model()


# ── Dashboard stats ─────────────────────────────────────────────────────────────

class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        today = timezone.localdate()
        total_messages_today = (
            DailyUsage.objects.filter(date=today).aggregate(total=Sum('messages_used'))['total'] or 0
        )
        data = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_agents': Agent.objects.count(),
            'enabled_agents': Agent.objects.filter(is_enabled=True).count(),
            'total_plans': Plan.objects.count(),
            'active_subscriptions': UserSubscription.objects.filter(
                status__in=[UserSubscription.Status.ACTIVE, UserSubscription.Status.TRIALING]
            ).count(),
            'total_chat_sessions': ChatSession.objects.count(),
            'total_messages_today': total_messages_today,
            'pending_safety_reports': SafetyReport.objects.filter(status=SafetyReport.Status.PENDING).count(),
        }
        return Response(AdminStatsSerializer(data).data)


# ── Users ────────────────────────────────────────────────────────────────────────

class AdminUserListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = User.objects.all()
        role = request.query_params.get('role')
        is_active = request.query_params.get('is_active')
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return Response(AdminUserSerializer(queryset, many=True).data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminUserSerializer(user).data)

    def patch(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_user_updated',
            request=request,
            object_type='User',
            object_id=pk,
            metadata={'updated_fields': list(serializer.validated_data.keys())},
        )
        return Response(AdminUserSerializer(user).data)


# ── Agents ─────────────────────────────────────────────────────────────────────

class AdminAgentListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        agents = Agent.objects.all()
        return Response(AdminAgentSerializer(agents, many=True).data)

    def post(self, request):
        serializer = AdminAgentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_agent_created',
            request=request,
            object_type='Agent',
            object_id=agent.id,
            metadata={'agent_key': agent.key},
        )
        return Response(AdminAgentSerializer(agent).data, status=status.HTTP_201_CREATED)


class AdminAgentDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_agent(self, key):
        try:
            return Agent.objects.get(key=key)
        except Agent.DoesNotExist:
            return None

    def get(self, request, key):
        agent = self._get_agent(key)
        if not agent:
            return Response({'detail': 'Agent not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminAgentSerializer(agent).data)

    def patch(self, request, key):
        agent = self._get_agent(key)
        if not agent:
            return Response({'detail': 'Agent not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminAgentSerializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_agent_updated',
            request=request,
            object_type='Agent',
            object_id=agent.id,
            metadata={'agent_key': agent.key, 'updated_fields': list(serializer.validated_data.keys())},
        )
        return Response(AdminAgentSerializer(agent).data)


# ── Plans ─────────────────────────────────────────────────────────────────────

class AdminPlanListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        plans = Plan.objects.all()
        return Response(AdminPlanSerializer(plans, many=True).data)

    def post(self, request):
        serializer = AdminPlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_plan_created',
            request=request,
            object_type='Plan',
            object_id=plan.id,
            metadata={'plan_code': plan.code},
        )
        return Response(AdminPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class AdminPlanDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_plan(self, code):
        try:
            return Plan.objects.get(code=code)
        except Plan.DoesNotExist:
            return None

    def get(self, request, code):
        plan = self._get_plan(code)
        if not plan:
            return Response({'detail': 'Plan not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminPlanSerializer(plan).data)

    def patch(self, request, code):
        plan = self._get_plan(code)
        if not plan:
            return Response({'detail': 'Plan not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_plan_updated',
            request=request,
            object_type='Plan',
            object_id=plan.id,
            metadata={'plan_code': plan.code, 'updated_fields': list(serializer.validated_data.keys())},
        )
        return Response(AdminPlanSerializer(plan).data)


# ── Subscriptions ─────────────────────────────────────────────────────────────

class AdminSubscriptionListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = UserSubscription.objects.select_related('user', 'plan').all()
        sub_status = request.query_params.get('status')
        provider = request.query_params.get('provider')
        if sub_status:
            queryset = queryset.filter(status=sub_status)
        if provider:
            queryset = queryset.filter(provider=provider)
        return Response(AdminSubscriptionSerializer(queryset, many=True).data)


# ── Safety reports ─────────────────────────────────────────────────────────────

class AdminSafetyReportListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = SafetyReport.objects.select_related('reported_by', 'reviewed_by').all()
        report_status = request.query_params.get('status')
        category = request.query_params.get('category')
        if report_status:
            queryset = queryset.filter(status=report_status)
        if category:
            queryset = queryset.filter(category=category)
        return Response(AdminSafetyReportSerializer(queryset, many=True).data)


class AdminSafetyReportDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_report(self, pk):
        try:
            return SafetyReport.objects.select_related('reported_by', 'reviewed_by').get(pk=pk)
        except SafetyReport.DoesNotExist:
            return None

    def get(self, request, pk):
        report = self._get_report(pk)
        if not report:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminSafetyReportSerializer(report).data)

    def patch(self, request, pk):
        report = self._get_report(pk)
        if not report:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSafetyReportReviewSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get('status')
        if new_status and new_status in [SafetyReport.Status.RESOLVED, SafetyReport.Status.DISMISSED,
                                          SafetyReport.Status.UNDER_REVIEW]:
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_safety_report_reviewed',
            request=request,
            object_type='SafetyReport',
            object_id=pk,
            metadata={'new_status': new_status},
        )
        return Response(AdminSafetyReportSerializer(report).data)


# ── App config ─────────────────────────────────────────────────────────────────

class AdminAppConfigListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        configs = AppConfig.objects.all()
        return Response(AdminAppConfigSerializer(configs, many=True).data)

    def post(self, request):
        serializer = AdminAppConfigCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_app_config_created',
            request=request,
            object_type='AppConfig',
            object_id=config.id,
            metadata={'key': config.key},
        )
        return Response(AdminAppConfigSerializer(config).data, status=status.HTTP_201_CREATED)


class AdminAppConfigDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_config(self, key):
        try:
            return AppConfig.objects.get(key=key)
        except AppConfig.DoesNotExist:
            return None

    def get(self, request, key):
        config = self._get_config(key)
        if not config:
            return Response({'detail': 'Config not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminAppConfigSerializer(config).data)

    def patch(self, request, key):
        config = self._get_config(key)
        if not config:
            return Response({'detail': 'Config not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminAppConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_app_config_updated',
            request=request,
            object_type='AppConfig',
            object_id=config.id,
            metadata={'key': config.key},
        )
        return Response(AdminAppConfigSerializer(config).data)


# ── Feature flags ──────────────────────────────────────────────────────────────

class AdminFeatureFlagListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        flags = FeatureFlag.objects.all()
        return Response(AdminFeatureFlagSerializer(flags, many=True).data)

    def post(self, request):
        serializer = AdminFeatureFlagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        flag = serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_feature_flag_created',
            request=request,
            object_type='FeatureFlag',
            object_id=flag.id,
            metadata={'key': flag.key},
        )
        return Response(AdminFeatureFlagSerializer(flag).data, status=status.HTTP_201_CREATED)


class AdminFeatureFlagDetailView(APIView):
    permission_classes = [IsAdminRole]

    def _get_flag(self, key):
        try:
            return FeatureFlag.objects.get(key=key)
        except FeatureFlag.DoesNotExist:
            return None

    def get(self, request, key):
        flag = self._get_flag(key)
        if not flag:
            return Response({'detail': 'Feature flag not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminFeatureFlagSerializer(flag).data)

    def patch(self, request, key):
        flag = self._get_flag(key)
        if not flag:
            return Response({'detail': 'Feature flag not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminFeatureFlagSerializer(flag, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        create_audit_log(
            user=request.user,
            event_type='admin_feature_flag_updated',
            request=request,
            object_type='FeatureFlag',
            object_id=flag.id,
            metadata={'key': flag.key, 'is_enabled': flag.is_enabled},
        )
        return Response(AdminFeatureFlagSerializer(flag).data)
