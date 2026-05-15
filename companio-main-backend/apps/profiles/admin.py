from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'display_name',
        'preferred_language',
        'timezone',
        'profile_completed',
        'memory_enabled',
        'personalization_enabled',
    ]
    list_filter = [
        'profile_completed',
        'memory_enabled',
        'personalization_enabled',
        'gender',
    ]
    search_fields = ['user__email', 'display_name', 'country']
