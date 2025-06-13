"""
Redirection vers la configuration Celery adaptée pour Windows
"""
import sys
import os

# Rediriger l'import vers notre configuration personnalisée
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from celery_config import app, debug_task

# Exporter les symboles pour l'autodécouverte des tâches
__all__ = ['app', 'debug_task']

# NOTE: Toute la configuration est maintenant dans le fichier celery_config.py
# à la racine du projet. Ne pas modifier ce fichier. 