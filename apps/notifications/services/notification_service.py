"""
Service for managing notifications.
"""
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationUserPreference,
    NotificationCategory, NotificationPriority, NotificationStatus,
    NotificationDeliveryMethod
)
from apps.notifications.services.firebase_service import FirebaseNotificationService


class NotificationService:
    """Service class for creating and managing notifications."""

    @staticmethod
    def create_notification(
            recipient,
            title,
            content,
            category=NotificationCategory.GENERAL,
            priority=NotificationPriority.NORMAL,
            delivery_methods=None,
            related_object=None,
            action_url=None,
            icon=None
        ):
        """
        Create a new notification for a user.
        
        Args:
            recipient: User receiving the notification
            title: Notification title
            content: Notification content
            category: NotificationCategory
            priority: NotificationPriority
            delivery_methods: List of delivery methods
            related_object: Object related to the notification
            action_url: URL for action
            icon: Icon name
            
        Returns:
            Notification: Created notification instance
        """
        # Set default delivery methods if none provided
        if delivery_methods is None:
            delivery_methods = [NotificationDeliveryMethod.APP]
        
        # Convert delivery methods list to string
        delivery_methods_str = ','.join(delivery_methods)
        
        # Prepare content type and object id if related object is provided
        content_type = None
        object_id = None
        
        if related_object:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = str(related_object.pk)
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            content=content,
            category=category,
            priority=priority,
            delivery_methods=delivery_methods_str,
            content_type=content_type,
            object_id=object_id,
            action_url=action_url,
            icon=icon
        )
        
        # Send push notification if needed
        if NotificationDeliveryMethod.PUSH in delivery_methods:
            try:
                # Essayer d'envoyer la notification via Firebase
                FirebaseNotificationService.send_notification(notification)
            except Exception as e:
                # Gérer l'erreur mais ne pas bloquer la création de la notification
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'envoi de la notification push: {str(e)}")
        
        # Mark as delivered for app notifications 
        # (they will be seen when user checks the app)
        notification.delivered = True
        notification.save(update_fields=['delivered'])
        
        return notification

    @staticmethod
    def create_from_template(
            template_code,
            recipient,
            context_data=None,
            related_object=None,
            action_url=None
        ):
        """
        Create a notification from a template.
        
        Args:
            template_code: Code of the template to use
            recipient: User receiving the notification
            context_data: Dict with data to format the template
            related_object: Object related to the notification
            action_url: URL for action
            
        Returns:
            Notification: Created notification instance
        """
        if context_data is None:
            context_data = {}
        
        try:
            template = NotificationTemplate.objects.get(code=template_code, is_active=True)
        except NotificationTemplate.DoesNotExist:
            raise ValueError(f"Template with code '{template_code}' not found or inactive")
        
        # Format title and content using context data
        title = template.title_template.format(**context_data)
        content = template.content_template.format(**context_data)
        
        # Get delivery methods from template
        delivery_methods = template.get_delivery_methods_list()
        
        # Create notification
        return NotificationService.create_notification(
            recipient=recipient,
            title=title,
            content=content,
            category=template.category,
            priority=template.priority,
            delivery_methods=delivery_methods,
            related_object=related_object,
            action_url=action_url,
            icon=template.default_icon
        )

    @staticmethod
    def get_user_notifications(user, status=None, category=None, limit=None):
        """
        Get notifications for a user with optional filtering.
        
        Args:
            user: User to get notifications for
            status: Optional status filter
            category: Optional category filter
            limit: Optional limit of notifications to return
            
        Returns:
            QuerySet: Filtered notifications
        """
        notifications = Notification.objects.filter(
            recipient=user,
            status__in=[NotificationStatus.UNREAD, NotificationStatus.READ]
        )
        
        if status:
            notifications = notifications.filter(status=status)
            
        if category:
            notifications = notifications.filter(category=category)
        
        if limit:
            notifications = notifications[:limit]
            
        return notifications

    @staticmethod
    def mark_as_read(notification_id, user):
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            user: User who owns the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def archive_notification(notification_id, user):
        """
        Archive a notification.
        
        Args:
            notification_id: ID of the notification
            user: User who owns the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.archive()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def delete_notification(notification_id, user):
        """
        Delete a notification (soft delete).
        
        Args:
            notification_id: ID of the notification
            user: User who owns the notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.delete_notification()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user, category=None):
        """
        Mark all user notifications as read.
        
        Args:
            user: User to mark notifications for
            category: Optional category filter
            
        Returns:
            int: Number of notifications marked as read
        """
        now = timezone.now()
        
        # Get unread notifications
        notifications = Notification.objects.filter(
            recipient=user,
            status=NotificationStatus.UNREAD
        )
        
        if category:
            notifications = notifications.filter(category=category)
        
        # Update in bulk
        count = notifications.count()
        notifications.update(status=NotificationStatus.READ, read_at=now, updated_at=now)
        
        return count 