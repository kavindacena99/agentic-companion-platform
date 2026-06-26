"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', include('apps.common.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/profile/', include('apps.profiles.urls')),
    path('api/agents/', include('apps.agents.urls')),
    path('api/usage/', include('apps.usage.urls')),
    path('api/chats/', include('apps.chats.urls')),
    path('api/safety-reports/', include('apps.safety.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/app-config/', include('apps.app_config.urls')),
    path('api/admin/', include('apps.admin_api.urls')),
    path('api/v1/chat/', include('apps.agent_gateway.urls')),
]
