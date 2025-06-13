# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
try:
    # Import depuis la configuration spécifique à Windows
    from celery_config import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    try:
        # Fallback vers l'import original
        from .celery import app as celery_app
        __all__ = ('celery_app',)
    except ImportError:
        # Celery pas encore configuré ou dépendances manquantes
        pass

# Ne pas importer depuis la racine pour éviter le conflit de noms
# Les imports depuis la racine ont été supprimés pour éviter les conflits
