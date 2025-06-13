"""
Service for managing notification preferences.
"""
from django.utils import timezone

from apps.notifications.models import (
    NotificationUserPreference, NotificationCategory,
    NotificationPriority, NotificationDeliveryMethod
)


class NotificationPreferencesService:
    """Service class for managing user notification preferences."""

    @staticmethod
    def get_or_create_preferences(user):
        """
        Get or create notification preferences for a user.
        
        Args:
            user: User to get preferences for
            
        Returns:
            NotificationUserPreference: User preferences instance
        """
        preferences, created = NotificationUserPreference.objects.get_or_create(user=user)
        return preferences

    @staticmethod
    def update_preferences(user, **preference_data):
        """
        Update user notification preferences.
        
        Args:
            user: User to update preferences for
            **preference_data: Preference fields to update
            
        Returns:
            NotificationUserPreference: Updated preferences instance
        """
        preferences = NotificationPreferencesService.get_or_create_preferences(user)
        
        # Update only provided fields
        for key, value in preference_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        preferences.save()
        return preferences

    @staticmethod
    def should_deliver_notification(user, category, priority, delivery_method):
        """
        Check if a notification should be delivered based on user preferences.
        
        Args:
            user: User to check preferences for
            category: Notification category
            priority: Notification priority
            delivery_method: Delivery method to use
            
        Returns:
            bool: Whether notification should be delivered
        """
        preferences = NotificationPreferencesService.get_or_create_preferences(user)
        
        # Check if the delivery method is enabled
        if not preferences.is_delivery_method_enabled(delivery_method):
            return False
        
        # Check if the category is enabled
        if not preferences.is_category_enabled(category):
            return False
        
        # Check if the priority is high enough
        priority_levels = {
            NotificationPriority.LOW: 0,
            NotificationPriority.NORMAL: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.URGENT: 3
        }
        
        min_priority = preferences.minimum_priority
        
        if priority_levels.get(priority, 0) < priority_levels.get(min_priority, 0):
            return False
        
        # Check quiet hours (if applicable)
        if delivery_method in [NotificationDeliveryMethod.PUSH, NotificationDeliveryMethod.SMS]:
            if preferences.quiet_hours_start and preferences.quiet_hours_end:
                # Skip non-urgent notifications during quiet hours
                if priority != NotificationPriority.URGENT:
                    now = timezone.localtime()
                    current_time = now.time()
                    
                    # Handle the case where quiet hours span midnight
                    if preferences.quiet_hours_start > preferences.quiet_hours_end:
                        if current_time >= preferences.quiet_hours_start or current_time <= preferences.quiet_hours_end:
                            return False
                    else:
                        if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                            return False
        
        return True 