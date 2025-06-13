"""
Test de base pour Celery sur Windows
"""
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

# Import l'application Celery
from celery_config import debug_task

if __name__ == '__main__':
    print("Test basique de Celery pour Windows...")
    
    # Exécution synchrone (sans worker)
    print("Exécution synchrone de la tâche (sans worker)...")
    result = debug_task()
    print(f"Résultat: {result}")
    print("✅ Tâche exécutée avec succès en mode synchrone!")
    
    print("\nPour tester avec le worker, assurez-vous qu'il est en cours d'exécution.")
    print("Utilisez le script 'start_celery_worker.bat' pour démarrer le worker.")
    print("Puis utilisez 'test_celery_windows.py' pour envoyer une tâche au worker.") 