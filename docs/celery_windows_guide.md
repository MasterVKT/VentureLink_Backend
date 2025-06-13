# Guide d'utilisation de Celery sur Windows pour VentureLink

## Introduction

Celery peut être difficile à configurer sur Windows en raison de limitations du système d'exploitation concernant les processus et les sémaphores. Ce guide explique comment utiliser Celery dans le projet VentureLink sur un environnement Windows.

## Configuration spécifique à Windows

La configuration de Celery pour Windows a été optimisée pour éviter les erreurs suivantes :
- `PermissionError: [WinError 5] Access is denied`
- `OSError: [WinError 6] The handle is invalid`
- Erreurs de connexion aux brokers (RabbitMQ/Redis)

Notre configuration utilise :
- **Broker en mémoire** : `memory://` au lieu de Redis/RabbitMQ
- **Worker Pool Solo** : un seul processus worker pour éviter les problèmes de multiprocesing
- **Options désactivées** : gossip, mingle et heartbeat désactivés

## Démarrage du Worker Celery

Pour démarrer le worker Celery :

```
start_celery_worker.bat
```

Ce script active l'environnement virtuel et démarre le worker avec les options appropriées pour Windows.

## Démarrage de Celery Beat (tâches périodiques)

Pour démarrer le scheduler Celery Beat :

```
start_celery_beat.bat
```

## Test du fonctionnement

Deux scripts de test sont disponibles :

1. **Test basique (sans worker)** :
   ```
   python test_celery_basic.py
   ```
   Ce script exécute une tâche de manière synchrone sans passer par le worker.

2. **Test avec worker** :
   ```
   python test_celery_windows.py
   ```
   Ce script envoie une tâche au worker Celery.

## Création de tâches Celery

Pour créer vos propres tâches Celery dans le projet :

1. Dans votre application Django (ex: `apps/your_app/tasks.py`), créez vos tâches :

```python
from celery import shared_task

@shared_task
def my_task(param1, param2):
    # Votre code ici
    return result
```

2. Pour appeler la tâche de manière asynchrone :

```python
from apps.your_app.tasks import my_task

# Exécution asynchrone (via worker)
result = my_task.delay(param1, param2)
# ou
result = my_task.apply_async(args=[param1, param2])

# Exécution synchrone (sans worker)
result = my_task(param1, param2)
```

## Considérations pour la production

La configuration actuelle est optimisée pour le développement sur Windows. Pour la production (sous Linux) :

1. Remplacez le broker en mémoire par Redis ou RabbitMQ :
   ```python
   app.conf.broker_url = 'redis://localhost:6379/0'
   app.conf.result_backend = 'redis://localhost:6379/0'
   ```

2. Vous pouvez utiliser des workers parallèles :
   ```
   celery -A celery_config worker --concurrency=4 -l info
   ```

## Dépannage

### Le worker ne démarre pas

- Vérifiez que vous utilisez le pool solo : `--pool=solo`
- Désactivez les fonctionnalités problématiques : `--without-gossip --without-mingle --without-heartbeat`

### Les tâches ne sont pas exécutées

- Vérifiez que le worker est bien démarré
- Assurez-vous que le broker URL est configuré sur 'memory://' 
- Vérifiez les logs du worker pour détecter d'éventuelles erreurs 