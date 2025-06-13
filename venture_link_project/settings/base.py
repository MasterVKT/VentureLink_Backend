"""
Base settings for venture_link_project project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key-for-development')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    'celery',
    
    # Custom apps
    'apps.core',
    'apps.users',
    'apps.projects',
    'apps.messaging',
    'apps.notifications.apps.NotificationsConfig',
    'apps.investments.apps.InvestmentsConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.FirebaseAuthenticationMiddleware',
    'apps.core.middleware.CurrencyConversionMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'venture_link_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'venture_link_project.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS settings
CORS_ALLOW_CREDENTIALS = True

# Firebase settings
FIREBASE_CONFIG = {
    'apiKey': os.environ.get('FIREBASE_API_KEY', ''),
    'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
    'projectId': os.environ.get('FIREBASE_PROJECT_ID', ''),
    'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
    'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
    'appId': os.environ.get('FIREBASE_APP_ID', ''),
    'measurementId': os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
    'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', ''),
}

# Redis settings
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache timeout
CACHE_TTL = 60 * 15  # 15 minutes

# Currency settings
DEFAULT_CURRENCY = 'EUR'
AVAILABLE_CURRENCIES = ['EUR', 'USD', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'HKD']
EXCHANGE_RATE_API_URL = os.environ.get('EXCHANGE_RATE_API_URL', 'https://api.exchangerate-api.com/v4/latest/')
EXCHANGE_RATE_API_KEY = os.environ.get('EXCHANGE_RATE_API_KEY', '')
CURRENCY_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

# Frontend URL for redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')

# Payment settings
PAYMENT_SANDBOX_MODE = os.environ.get('PAYMENT_SANDBOX_MODE', 'True').lower() == 'true'
MYCOOLPAY_SANDBOX_PUBLIC_KEY = os.environ.get('MYCOOLPAY_SANDBOX_PUBLIC_KEY', '')
MYCOOLPAY_SANDBOX_PRIVATE_KEY = os.environ.get('MYCOOLPAY_SANDBOX_PRIVATE_KEY', '')
MYCOOLPAY_PUBLIC_KEY = os.environ.get('MYCOOLPAY_PUBLIC_KEY', '')
MYCOOLPAY_PRIVATE_KEY = os.environ.get('MYCOOLPAY_PRIVATE_KEY', '')
MYCOOLPAY_SANDBOX_WEBHOOK_SECRET = os.environ.get('MYCOOLPAY_SANDBOX_WEBHOOK_SECRET', '')
MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET = os.environ.get('MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET', '')
MYCOOLPAY_ALLOWED_IPS = os.environ.get('MYCOOLPAY_ALLOWED_IPS', '').split(',')
MYCOOLPAY_LIVE_MODE = not PAYMENT_SANDBOX_MODE

# Site URL for callbacks
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000') 