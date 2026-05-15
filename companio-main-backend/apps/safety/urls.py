from django.urls import path

from .views import MySafetyReportsView, SafetyReportCreateView

urlpatterns = [
    path('', SafetyReportCreateView.as_view(), name='safety-report-create'),
    path('my/', MySafetyReportsView.as_view(), name='safety-report-my'),
]
