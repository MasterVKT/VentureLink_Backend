"""
Serializers for notification models.
"""
from rest_framework import serializers

from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationUserPreference,
    NotificationCategory, NotificationPriority, NotificationStatus,
    NotificationDeliveryMethod
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'title', 'content', 'category', 'priority',
            'status', 'read_at', 'delivery_methods', 'delivered',
            'content_type', 'object_id', 'action_url', 'icon',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'category', 'priority',
            'status', 'read_at', 'icon', 'action_url', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'code', 'name', 'category', 'title_template',
            'content_template', 'priority', 'default_icon',
            'default_delivery_methods', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationUserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences."""
    
    class Meta:
        model = NotificationUserPreference
        fields = [
            'id', 'user', 'enable_email', 'enable_push', 'enable_sms',
            'enable_app', 'project_notifications', 'investment_notifications',
            'message_notifications', 'payment_notifications', 'system_notifications',
            'quiet_hours_start', 'quiet_hours_end', 'minimum_priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at'] 