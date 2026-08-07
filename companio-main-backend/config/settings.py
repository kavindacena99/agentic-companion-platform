import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_list(name, default=''):
    return [
        item.strip()
        for item in os.getenv(name, default).split(',')
        if item.strip()
    ]


def env_required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f'{name} must be set in the environment.')
    return value


def env_bool(name, default='False'):
    return os.getenv(name, default).lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default):
    return int(os.getenv(name, default))


SECRET_KEY = env_required('SECRET_KEY')
DEBUG = env_bool('DEBUG')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'apps.common',
    'apps.accounts',
    'apps.profiles',
    'apps.agent_gateway',
    'apps.agents',
    'apps.usage',
    'apps.chats',
    'apps.safety',
    'apps.subscriptions',
    'apps.notifications',
    'apps.app_config',
    'apps.audit_logs',
    'apps.admin_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env_required('DB_NAME'),
        'USER': env_required('DB_USER'),
        'PASSWORD': env_required('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Colombo')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5173',
)

AGENT_PLATFORM_BASE_URL = os.getenv(
    'AGENT_PLATFORM_BASE_URL',
    'http://127.0.0.1:9000',
)
AGENT_PLATFORM_SERVICE_KEY = os.getenv('AGENT_PLATFORM_SERVICE_KEY', '')
AGENT_PLATFORM_TIMEOUT_SECONDS = env_int('AGENT_PLATFORM_TIMEOUT_SECONDS', 5)
AGENT_PLATFORM_USE_MOCK = env_bool('AGENT_PLATFORM_USE_MOCK', 'True')
FREE_DAILY_MESSAGE_LIMIT = env_int('FREE_DAILY_MESSAGE_LIMIT', 20)

# agent-core (AI Agent Platform Backend) — used by the chat gateway endpoint.
AGENT_CORE_URL = os.getenv('AGENT_CORE_URL', 'http://localhost:8001')
AGENT_CORE_TIMEOUT_SECONDS = env_int('AGENT_CORE_TIMEOUT_SECONDS', 30)
AGENT_CORE_SERVICE_KEY = os.getenv('AGENT_CORE_SERVICE_KEY', '')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        'auth': '5/minute',
        'chat': '20/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env_int('JWT_ACCESS_TOKEN_MINUTES', 30)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env_int('JWT_REFRESH_TOKEN_DAYS', 7)),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ---------------------------------------------------------------------------
# Production security hardening
#
# These are toggled by NOT being in DEBUG mode. In development (DEBUG=True)
# they are inactive so local HTTP works normally.
# ---------------------------------------------------------------------------
if not DEBUG:
    # HTTPS / HSTS
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    # Miscellaneous headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

