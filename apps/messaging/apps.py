"""
Application configuration for messaging app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MessagingConfig(AppConfig):
    """
    Configuration for the messaging application.
    """
    name = 'apps.messaging'
    verbose_name = _('Messagerie')
    verbose_name_plural = _('Messagerie')

    def ready(self):
        """
        Initialize signals.
        """
        import apps.messaging.signals  # noqa 