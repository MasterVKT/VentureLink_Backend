"""
URLs pour l'application content.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.content.views import (
    CommentViewSet, CommentLikeViewSet,
    PublicationViewSet, PublicationMediaViewSet, PublicationLikeViewSet
)

# Router pour les API REST
router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'comment-likes', CommentLikeViewSet, basename='comment-like')
router.register(r'publications', PublicationViewSet, basename='publication')
router.register(r'publication-media', PublicationMediaViewSet, basename='publication-media')
router.register(r'publication-likes', PublicationLikeViewSet, basename='publication-like')

app_name = 'content'

urlpatterns = [
    path('api/', include(router.urls)),
] 