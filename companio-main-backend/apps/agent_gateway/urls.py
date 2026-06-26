from django.urls import path

from .views import ChatGatewayView

urlpatterns = [
    path('', ChatGatewayView.as_view(), name='chat-gateway'),
]
