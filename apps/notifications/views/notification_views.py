"""
API views for notification management.
"""
from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationUserPreference,
    NotificationCategory, NotificationStatus
)
from apps.notifications.serializers import (
    NotificationSerializer, NotificationListSerializer,
    NotificationTemplateSerializer, NotificationUserPreferenceSerializer
)
from apps.notifications.services import NotificationService, NotificationPreferencesService
from apps.core.permissions import IsAdminUser


class NotificationViewSet(mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """
    API endpoint for user notifications.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'priority']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return notifications for the current user."""
        return Notification.objects.filter(
            recipient=self.request.user,
            status__in=[NotificationStatus.UNREAD, NotificationStatus.READ]
        )
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views."""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        success = NotificationService.mark_as_read(pk, request.user)
        if success:
            return Response({'status': 'notification marked as read'})
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a notification."""
        success = NotificationService.archive_notification(pk, request.user)
        if success:
            return Response({'status': 'notification archived'})
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        category = request.data.get('category', None)
        count = NotificationService.mark_all_as_read(request.user, category)
        return Response({'status': f'{count} notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = Notification.objects.filter(
            recipient=request.user,
            status=NotificationStatus.UNREAD
        ).count()
        return Response({'unread_count': count})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for notification templates.
    Admin only.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']


class NotificationPreferenceViewSet(mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin,
                                    mixins.ListModelMixin,
                                    viewsets.GenericViewSet):
    """
    API endpoint for user notification preferences.
    """
    serializer_class = NotificationUserPreferenceSerializer
    permission_classes = []  # Permissions gérées au niveau des actions

    def get_object(self):
        """Get or create preferences for the current user."""
        return NotificationPreferencesService.get_or_create_preferences(self.request.user)
    
    def get_queryset(self):
        """Return preferences for the current user only."""
        # Pour l'action list, on retourne juste les préférences de l'utilisateur actuel
        preferences = NotificationPreferencesService.get_or_create_preferences(self.request.user)
        return NotificationUserPreference.objects.filter(id=preferences.id)
    
    def list(self, request, *args, **kwargs):
        """Return user preferences."""
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentification requise."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        preferences = self.get_object()
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user preferences."""
        preferences = self.get_object()
        serializer = self.get_serializer(preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update preferences with validated data
        preferences = NotificationPreferencesService.update_preferences(
            request.user, **serializer.validated_data
        )
        
        return Response(self.get_serializer(preferences).data) 