"""
URL patterns for the users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    UserViewSet, ProfileViewSet, SubscriptionViewSet
)

# Configuration du routeur
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]

