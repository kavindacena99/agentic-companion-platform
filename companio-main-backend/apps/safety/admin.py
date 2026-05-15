from django.contrib import admin

from .models import SafetyReport


@admin.register(SafetyReport)
class SafetyReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'status', 'reported_by', 'message', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['reported_by__email', 'message__agent_request_id', 'description']
    autocomplete_fields = ['reported_by', 'reviewed_by', 'session', 'message']
