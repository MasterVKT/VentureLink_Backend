"""
Signal handlers for the notifications application.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.users.models import User
from apps.notifications.models import NotificationUserPreference


@receiver(post_save, sender=User)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """
    Create notification preferences when a new user is created.
    
    Args:
        sender: The model class
        instance: The actual instance being saved
        created: Boolean; True if a new record was created
    """
    if created:
        NotificationUserPreference.objects.create(user=instance) 