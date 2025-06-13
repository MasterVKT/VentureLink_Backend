"""
URLs pour les APIs de l'application users.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    UserViewSet, ProfileViewSet, SubscriptionViewSet, DeviceTokenViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'device-tokens', DeviceTokenViewSet, basename='device-token')

urlpatterns = [
    path('', include(router.urls)),
] 