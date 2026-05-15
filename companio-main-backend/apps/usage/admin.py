from django.contrib import admin

from .models import DailyUsage


@admin.register(DailyUsage)
class DailyUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'messages_used', 'message_limit']
    list_filter = ['date']
    search_fields = ['user__email', 'user__username']
