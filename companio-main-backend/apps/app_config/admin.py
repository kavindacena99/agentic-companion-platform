from django.contrib import admin

from .models import AppConfig, FeatureFlag


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_type', 'is_public', 'is_active', 'updated_at']
    list_filter = ['value_type', 'is_public', 'is_active']
    search_fields = ['key', 'description']


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'is_enabled', 'rollout_percentage', 'is_public']
    list_filter = ['is_enabled', 'is_public']
    search_fields = ['key', 'name', 'description']
