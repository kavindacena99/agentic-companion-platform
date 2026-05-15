from .models import AppConfig, FeatureFlag


def _parse_config_value(config):
    value = config.value
    if config.value_type == AppConfig.ValueType.BOOLEAN:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {'1', 'true', 'yes', 'on'}
    if config.value_type == AppConfig.ValueType.INTEGER:
        return int(value)
    if config.value_type == AppConfig.ValueType.DECIMAL:
        return str(value)
    return value


def get_public_app_config():
    return {
        config.key: _parse_config_value(config)
        for config in AppConfig.objects.filter(is_public=True, is_active=True)
    }


def get_feature_flags(public_only=True):
    queryset = FeatureFlag.objects.all()
    if public_only:
        queryset = queryset.filter(is_public=True)
    return {flag.key: flag.is_enabled for flag in queryset}


def is_feature_enabled(key):
    flag = FeatureFlag.objects.filter(key=key).first()
    return bool(flag and flag.is_enabled)


def get_config_value(key, default=None):
    config = AppConfig.objects.filter(key=key, is_active=True).first()
    if not config:
        return default
    return _parse_config_value(config)
