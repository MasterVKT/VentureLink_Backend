"""
URL patterns pour l'application core.
"""
from django.urls import path

from apps.core.views import CurrencyListView, test_sentry


urlpatterns = [
    path('currencies/', CurrencyListView.as_view(), name='currency-list'),
    path('test-sentry/', test_sentry, name='test-sentry'),
] 