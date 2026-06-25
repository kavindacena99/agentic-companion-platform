from django.urls import path

from .views import (
    AdminAgentDetailView,
    AdminAgentListView,
    AdminAppConfigDetailView,
    AdminAppConfigListView,
    AdminFeatureFlagDetailView,
    AdminFeatureFlagListView,
    AdminPlanDetailView,
    AdminPlanListView,
    AdminSafetyReportDetailView,
    AdminSafetyReportListView,
    AdminStatsView,
    AdminSubscriptionListView,
    AdminUserDetailView,
    AdminUserListView,
)

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('agents/', AdminAgentListView.as_view(), name='admin-agent-list'),
    path('agents/<slug:key>/', AdminAgentDetailView.as_view(), name='admin-agent-detail'),
    path('plans/', AdminPlanListView.as_view(), name='admin-plan-list'),
    path('plans/<slug:code>/', AdminPlanDetailView.as_view(), name='admin-plan-detail'),
    path('subscriptions/', AdminSubscriptionListView.as_view(), name='admin-subscription-list'),
    path('safety-reports/', AdminSafetyReportListView.as_view(), name='admin-safety-report-list'),
    path('safety-reports/<int:pk>/', AdminSafetyReportDetailView.as_view(), name='admin-safety-report-detail'),
    path('app-config/', AdminAppConfigListView.as_view(), name='admin-app-config-list'),
    path('app-config/<slug:key>/', AdminAppConfigDetailView.as_view(), name='admin-app-config-detail'),
    path('feature-flags/', AdminFeatureFlagListView.as_view(), name='admin-feature-flag-list'),
    path('feature-flags/<slug:key>/', AdminFeatureFlagDetailView.as_view(), name='admin-feature-flag-detail'),
]
