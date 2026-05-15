from django.contrib import admin

from .models import ChatMessage, ChatSession


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'agent', 'title', 'status', 'last_message_at', 'started_at']
    list_filter = ['status', 'agent']
    search_fields = ['user__email', 'agent__key', 'title']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'sender', 'status', 'safety_status', 'created_at']
    list_filter = ['sender', 'status', 'safety_status']
    search_fields = ['session__user__email', 'agent_request_id']
