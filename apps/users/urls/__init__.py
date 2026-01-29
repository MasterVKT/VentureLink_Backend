"""
URL patterns for the users app.
"""
from django.urls import path, include, re_path
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
    # Route directe pour l'utilisateur actuel
    path('me/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), {'pk': 'me'}, name='user-me'),
    # Route directe pour le FCM token (avec pattern regex pour gérer avec/sans slash)
    re_path(r'^fcm-token/?$', UserViewSet.as_view({'post': 'update_fcm_token'}), name='user-fcm-token'),
    path('', include(router.urls)),
]

