"""
Script de test pour Celery sous Windows
"""
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

# Import l'application Celery
from celery_config import app, debug_task

if __name__ == '__main__':
    print("Envoi d'une tâche de test Celery spécifique pour Windows...")
    print(f"Broker URL configuré: {app.conf.broker_url}")
    
    # Forcer la config à nouveau
    app.conf.task_always_eager = False
    app.conf.broker_url = 'memory://'
    app.conf.broker_connection_retry = False
    
    # Envoi de la tâche de debug sans attendre le résultat
    result = debug_task.apply_async()
    
    print(f"Tâche envoyée avec l'ID: {result.id}")
    print("La tâche a été envoyée avec succès au worker.")
    print("Vérifiez les logs du worker pour voir le résultat.")
    
    print("\nNote: Assurez-vous que le worker Celery est en cours d'exécution.")
    print("Vous pouvez démarrer le worker avec le script 'start_celery_worker.bat'")
    print("\nConfiguration spécifique Windows:")
    print(" - Broker: memory:// (broker en mémoire)")
    print(" - Worker pool: solo (un seul processus)")
    print(" - Heartbeat, gossip, mingle: désactivés")
    print(" - Concurrency: 1 (pas de processus parallèles)") 