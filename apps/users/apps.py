from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Utilisateurs'
    
    def ready(self):
        """Importer les signaux lors du chargement de l'application."""
        import apps.users.signals 