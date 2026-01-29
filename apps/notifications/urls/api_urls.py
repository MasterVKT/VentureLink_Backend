"""
API URL configuration for the notifications app.
"""
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    NotificationViewSet, NotificationTemplateViewSet, NotificationPreferenceViewSet
)

# Configuration du routeur pour les viewsets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notification-template')
# notification-preferences géré par route directe en bas

urlpatterns = [
    # Route directe pour les préférences utilisateur (avec pattern regex pour gérer avec/sans slash)
    re_path(r'^notification-preferences/?$', NotificationPreferenceViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'partial_update'}), name='notification-preferences'),
    path('', include(router.urls)),
] 