from django.contrib import admin

from .models import Agent, UserAgentSelection


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'key',
        'display_name',
        'agent_type',
        'is_enabled',
        'is_premium',
        'sort_order',
    ]
    list_filter = ['agent_type', 'is_enabled', 'is_premium']
    search_fields = ['key', 'display_name', 'short_description']
    ordering = ['sort_order', 'display_name']


@admin.register(UserAgentSelection)
class UserAgentSelectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent', 'is_active', 'selected_at']
    list_filter = ['is_active', 'agent']
    search_fields = ['user__email', 'agent__key', 'agent__display_name']
    autocomplete_fields = ['user', 'agent']
