"""
Script de test pour Celery
"""
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

# Import l'application Celery
from celery_config import app, debug_task

if __name__ == '__main__':
    print("Envoi d'une tâche de test Celery...")
    
    # Envoi de la tâche de debug
    result = debug_task.delay()
    
    print(f"Tâche envoyée avec l'ID: {result.id}")
    print("Vérifiez les logs du worker Celery pour voir le résultat.")
    print("\nNote: Assurez-vous que le worker Celery est en cours d'exécution.")
    print("Vous pouvez démarrer le worker avec le script 'start_celery_worker.bat'") 