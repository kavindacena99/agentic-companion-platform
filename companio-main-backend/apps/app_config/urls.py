from django.urls import path

from .views import PublicAppConfigView

urlpatterns = [
    path('public/', PublicAppConfigView.as_view(), name='app-config-public'),
]
