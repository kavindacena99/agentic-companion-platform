from django.urls import path

from .views import CurrentSubscriptionView, PlanListView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='subscription-plans'),
    path('me/', CurrentSubscriptionView.as_view(), name='subscription-me'),
]
