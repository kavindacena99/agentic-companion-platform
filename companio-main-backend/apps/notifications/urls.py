from django.urls import path

from .views import DeviceTokenView, NotificationPreferenceView

urlpatterns = [
    path('device-token/', DeviceTokenView.as_view(), name='notification-device-token'),
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
]
