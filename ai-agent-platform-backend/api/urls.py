"""URL routes for the REST API layer."""

from django.urls import path

from api.chat import ChatView
from api.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("chat/", ChatView.as_view(), name="chat"),
]
