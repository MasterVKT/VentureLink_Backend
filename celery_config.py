"""
Configuration Celery pour VentureLink - Spécifique à Windows
"""
import os
from celery import Celery

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')

# Création de l'application Celery sans aucun broker
app = Celery('venture_link_project')

# Configuration explicite pour forcer l'utilisation du broker en mémoire
app.conf.update(
    broker_url='memory://',
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=0,
    broker_heartbeat=None,
    broker_pool_limit=0,
    result_backend=None,
    task_ignore_result=True,
    
    # Configuration de base
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    
    # Configuration Windows spécifique
    worker_pool='solo',
    worker_prefetch_multiplier=1,
    worker_concurrency=1,
    worker_max_tasks_per_child=1,
    worker_cancel_long_running_tasks_on_connection_loss=False,
    
    # Désactiver les fonctionnalités qui peuvent causer des problèmes
    worker_send_task_events=False,
    task_send_sent_event=False,
    event_queue_expires=60,
    worker_enable_remote_control=False
)

# Autodiscovery des tâches dans toutes les apps Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Tâche de debug pour tester Celery"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!' 