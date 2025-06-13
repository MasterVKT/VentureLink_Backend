"""
Settings pour l'environnement de test.
"""
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-test-key-not-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}

# Désactiver les middlewares inutiles en test
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Test runner personnalisé pour désactiver Firebase
TEST_RUNNER = 'apps.core.test_utils.NoFirebaseTestRunner'

# Désactiver la sécurité en test
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactiver le throttling
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Faciliter les tests d'API
REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

# Configuration des API externes pour les tests
EXTERNAL_APIS = {
    'MY_COOL_PAY': {
        'API_KEY': 'test_api_key',
        'SECRET_KEY': 'test_secret_key',
        'BASE_URL': 'https://sandbox.mycoolpay.com/api/v1',
        'WEBHOOK_SECRET': 'test_webhook_secret',
    },
    'CURRENCY_EXCHANGE': {
        'API_KEY': 'test_api_key',
        'BASE_URL': 'https://sandbox.currencyapi.com/v1',
    }
}

# Configuration Firebase pour les tests
FIREBASE_CONFIG = {
    'SERVICE_ACCOUNT_KEY_PATH': 'config/firebase-admin-sdk-test.json',
    'DATABASE_URL': 'https://venture-link-test.firebaseio.com',
    'STORAGE_BUCKET': 'venture-link-test.appspot.com',
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Django cache for testing (in-memory cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable migrations for faster tests
class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Firebase SDK path (use test credentials)
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'config/firebase-admin-sdk-test.json') 