from django.urls import path

from .views import (
    AgentDetailView,
    AgentListView,
    SelectAgentView,
    SelectedAgentView,
)

urlpatterns = [
    path('', AgentListView.as_view(), name='agent-list'),
    path('select/', SelectAgentView.as_view(), name='agent-select'),
    path('selected/', SelectedAgentView.as_view(), name='agent-selected'),
    path('<int:pk>/', AgentDetailView.as_view(), name='agent-detail'),
]
