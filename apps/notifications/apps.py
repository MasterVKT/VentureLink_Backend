"""
Application configuration for notifications app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    """
    Configuration for the notifications application.
    """
    name = 'apps.notifications'
    verbose_name = _('Notifications')
    verbose_name_plural = _('Notifications')

    def ready(self):
        """
        Initialize signals.
        """
        import apps.notifications.signals  # noqa 