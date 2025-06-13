"""
Admin configuration for notifications app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationUserPreference
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    list_display = ('title', 'recipient', 'category', 'priority', 'status', 'created_at')
    list_filter = ('status', 'category', 'priority', 'created_at')
    search_fields = ('title', 'content', 'recipient__email')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('recipient',)
    date_hierarchy = 'created_at'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationTemplate model."""
    list_display = ('code', 'name', 'category', 'priority', 'is_active')
    list_filter = ('category', 'priority', 'is_active')
    search_fields = ('code', 'name', 'title_template', 'content_template')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NotificationUserPreference)
class NotificationUserPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationUserPreference model."""
    list_display = ('user', 'enable_email', 'enable_push', 'enable_sms', 'enable_app')
    list_filter = ('enable_email', 'enable_push', 'enable_sms', 'enable_app')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',) 