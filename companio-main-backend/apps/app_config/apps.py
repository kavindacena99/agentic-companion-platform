from django.apps import AppConfig as DjangoAppConfig


class AppConfigConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.app_config'
    label = 'app_config'
