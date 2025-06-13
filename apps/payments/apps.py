"""
Configuration de l'application payments.
"""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration de l'application de gestion des paiements."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Gestion des Paiements'
    
    def ready(self):
        """Initialisation de l'application à son démarrage."""
        import apps.payments.signals  # noqa
