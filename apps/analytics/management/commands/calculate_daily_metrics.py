"""
Commande pour calculer les métriques quotidiennes.
"""
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande pour calculer les métriques quotidiennes de la plateforme.
    
    Cette commande peut être utilisée manuellement ou programmée pour s'exécuter
    quotidiennement via une tâche cron ou un planificateur Celery.
    """
    
    help = "Calcule et enregistre les métriques quotidiennes de la plateforme"
    
    def add_arguments(self, parser):
        """Ajouter les arguments de la commande."""
        parser.add_argument(
            '--date',
            type=str,
            help='Date pour laquelle calculer les métriques (format YYYY-MM-DD, par défaut: hier)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Nombre de jours à calculer en remontant dans le temps'
        )
    
    def handle(self, *args, **options):
        """Exécuter la commande."""
        date_str = options.get('date')
        days = options.get('days')
        
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR(
                    f"Format de date invalide: {date_str}. Utilisez le format YYYY-MM-DD."
                ))
                return
        else:
            # Calculer pour la veille par défaut (les données du jour courant seraient incomplètes)
            target_date = timezone.now().date() - timedelta(days=1)
        
        # Calculer pour plusieurs jours si spécifié
        for i in range(days):
            date_to_calculate = target_date - timedelta(days=i)
            try:
                metrics = MetricsService.calculate_daily_metrics(date_to_calculate)
                self.stdout.write(self.style.SUCCESS(
                    f"Métriques calculées avec succès pour le {date_to_calculate}: "
                    f"{metrics.new_users_count} nouveaux utilisateurs, "
                    f"{metrics.active_users_count} utilisateurs actifs"
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"Erreur lors du calcul des métriques pour le {date_to_calculate}: {str(e)}"
                ))
        
        if days > 1:
            self.stdout.write(self.style.SUCCESS(
                f"Calcul terminé pour {days} jours à partir du {target_date}"
            )) 