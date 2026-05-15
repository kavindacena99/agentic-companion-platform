from django.urls import path

from .views import CurrentUsageView

urlpatterns = [
    path('me/', CurrentUsageView.as_view(), name='usage-me'),
]
