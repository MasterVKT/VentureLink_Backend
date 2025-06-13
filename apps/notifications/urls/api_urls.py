"""
API URL configuration for the notifications app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    NotificationViewSet, NotificationTemplateViewSet, NotificationPreferenceViewSet
)

# Configuration du routeur pour les viewsets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
] 