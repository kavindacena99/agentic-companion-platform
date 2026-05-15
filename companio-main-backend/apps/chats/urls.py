from django.urls import path

from .views import (
    ChatSessionDetailView,
    ChatSessionListCreateView,
    ChatSessionMessagesView,
)

urlpatterns = [
    path('sessions/', ChatSessionListCreateView.as_view(), name='chat-session-list'),
    path('sessions/<int:session_id>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
    path(
        'sessions/<int:session_id>/messages/',
        ChatSessionMessagesView.as_view(),
        name='chat-session-messages',
    ),
]
