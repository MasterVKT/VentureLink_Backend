"""
Tâches Celery pour le calcul et la mise à jour des métriques.
"""
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone

from apps.analytics.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


@shared_task
def calculate_daily_metrics(date_str=None):
    """
    Calcule les métriques quotidiennes pour une date donnée.
    
    Si aucune date n'est fournie, calcule les métriques de la veille.
    
    Args:
        date_str: Date pour laquelle calculer les métriques (format YYYY-MM-DD)
        
    Returns:
        str: Message de confirmation avec les métriques calculées
    """
    try:
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Format de date invalide: {date_str}. Utilisation de la date d'hier.")
                date = timezone.now().date() - timedelta(days=1)
        else:
            # Utiliser la date d'hier par défaut
            date = timezone.now().date() - timedelta(days=1)
        
        metrics = MetricsService.calculate_daily_metrics(date)
        
        message = (
            f"Métriques calculées avec succès pour le {date}: "
            f"{metrics.new_users_count} nouveaux utilisateurs, "
            f"{metrics.active_users_count} utilisateurs actifs, "
            f"{metrics.new_projects_count} nouveaux projets"
        )
        
        logger.info(message)
        return message
    
    except Exception as e:
        error_message = f"Erreur lors du calcul des métriques quotidiennes: {str(e)}"
        logger.error(error_message)
        raise Exception(error_message)


@shared_task
def recalculate_historical_metrics(days=30):
    """
    Recalcule les métriques historiques pour un nombre de jours donné.
    
    Cette tâche est utile pour remplir l'historique des métriques
    ou les recalculer après une modification du code.
    
    Args:
        days: Nombre de jours dans le passé à recalculer
        
    Returns:
        str: Message de confirmation
    """
    try:
        end_date = timezone.now().date() - timedelta(days=1)  # Hier
        start_date = end_date - timedelta(days=days-1)
        
        recalculated_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            MetricsService.calculate_daily_metrics(current_date)
            recalculated_count += 1
            current_date += timedelta(days=1)
        
        message = f"Recalcul terminé pour {recalculated_count} jours du {start_date} au {end_date}"
        logger.info(message)
        return message
    
    except Exception as e:
        error_message = f"Erreur lors du recalcul des métriques historiques: {str(e)}"
        logger.error(error_message)
        raise Exception(error_message) 