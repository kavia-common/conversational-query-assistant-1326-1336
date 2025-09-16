"""
Django settings for config project.

Lightweight REST API for a chatbot that calls OpenAI. No database or persistence.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-0ku_as45vs5isd^px=t#m8g#^*x7f=w#gw-xb^t@^-pom)r^t6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow hosts:
# - Prefer ALLOWED_HOSTS environment variable (comma-separated values).
# - Fallback to permissive defaults for development, including wildcard when explicitly desired.
# Note: In production, set ALLOWED_HOSTS env var explicitly (e.g., "api.example.com").
_raw_allowed_hosts = os.getenv("ALLOWED_HOSTS", "").strip()

if _raw_allowed_hosts:
    # Split by comma, strip whitespace, ignore empties
    ALLOWED_HOSTS = [h.strip() for h in _raw_allowed_hosts.split(",") if h.strip()]
else:
    # Development defaults; can include wildcard if desired to avoid 'Invalid Host header'
    # Keeping common local hosts and testserver for Django test client.
    ALLOWED_HOSTS = [
        "*",              # allow all in dev; override via env in prod
        ".kavia.ai",
        "localhost",
        "127.0.0.1",
        "testserver",
        "chatbot_frontend",
    ]

# Application definition
# Remove admin/auth/session apps to avoid DB dependency, keep minimal stack
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # intentionally excluding sessions/auth/csrf to keep it stateless and avoid DB usage
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Explicitly disable database usage by providing an empty DATABASES dict
DATABASES = {}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (used for docs UI assets if needed)
STATIC_URL = 'static/'

# REST Framework defaults
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'UNAUTHENTICATED_USER': None,
}

# CORS for local frontend access
CORS_ALLOW_ALL_ORIGINS = True

# Proxy/hosting headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
X_FRAME_OPTIONS = 'ALLOWALL'
