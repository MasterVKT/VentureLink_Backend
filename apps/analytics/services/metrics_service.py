"""
Service pour la gestion des métriques et statistiques.
"""
import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.contrib.auth import get_user_model

from apps.analytics.models import UserMetrics, ProjectMetrics, DailyMetrics, EventLog
from apps.projects.models import Project, ProjectInterest, ProjectFavorite
from apps.investments.models import Investment
from apps.payments.models import Payment, UserSubscription

User = get_user_model()
logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service pour calculer, mettre à jour et récupérer les métriques.
    """
    
    @staticmethod
    def calculate_daily_metrics(date=None):
        """
        Calcule et enregistre les métriques quotidiennes pour une date donnée.
        
        Args:
            date: Date pour laquelle calculer les métriques (aujourd'hui par défaut)
            
        Returns:
            DailyMetrics: L'objet de métriques quotidiennes créé ou mis à jour
        """
        # Utiliser la date d'aujourd'hui si non spécifiée
        if date is None:
            date = timezone.now().date()
        
        # Définir les plages de temps pour les requêtes
        day_start = datetime.combine(date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        
        # Requêtes pour récupérer les données
        new_users_count = User.objects.filter(date_joined__range=(day_start, day_end)).count()
        
        active_users_count = EventLog.objects.filter(
            created_at__range=(day_start, day_end)
        ).values('user').distinct().count()
        
        new_projects = Project.objects.filter(created_at__range=(day_start, day_end))
        new_projects_count = new_projects.count()
        
        published_projects_count = new_projects.filter(is_published=True).count()
        
        total_views = EventLog.objects.filter(
            event_type=EventLog.EventType.PROJECT_VIEW,
            created_at__range=(day_start, day_end)
        ).count()
        
        total_interests = EventLog.objects.filter(
            event_type=EventLog.EventType.PROJECT_INTEREST,
            created_at__range=(day_start, day_end)
        ).count()
        
        investments = Investment.objects.filter(created_at__range=(day_start, day_end))
        total_investment_amount = investments.aggregate(total=Sum('amount'))['total'] or 0
        
        new_subscriptions = UserSubscription.objects.filter(
            start_date__range=(day_start, day_end),
            status='ACTIVE'
        )
        new_subscriptions_count = new_subscriptions.count()
        
        subscription_payments = Payment.objects.filter(
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            status=Payment.PaymentStatus.COMPLETED,
            created_at__range=(day_start, day_end)
        )
        subscription_revenue = subscription_payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Créer ou mettre à jour les métriques quotidiennes
        with transaction.atomic():
            daily_metrics, created = DailyMetrics.objects.update_or_create(
                date=date,
                defaults={
                    'new_users_count': new_users_count,
                    'active_users_count': active_users_count,
                    'new_projects_count': new_projects_count,
                    'published_projects_count': published_projects_count,
                    'total_views_count': total_views,
                    'total_interests_count': total_interests,
                    'total_investment_amount': total_investment_amount,
                    'new_subscriptions_count': new_subscriptions_count,
                    'subscription_revenue': subscription_revenue
                }
            )
            
            if created:
                logger.info(f"Métriques quotidiennes créées pour le {date}")
            else:
                logger.info(f"Métriques quotidiennes mises à jour pour le {date}")
            
            return daily_metrics
    
    @staticmethod
    def get_user_metrics(user):
        """
        Récupère les métriques d'un utilisateur, les crée si elles n'existent pas.
        
        Args:
            user: L'utilisateur dont on veut les métriques
            
        Returns:
            UserMetrics: Les métriques de l'utilisateur
        """
        metrics, created = UserMetrics.objects.get_or_create(user=user)
        return metrics
    
    @staticmethod
    def get_project_metrics(project):
        """
        Récupère les métriques d'un projet, les crée si elles n'existent pas.
        
        Args:
            project: Le projet dont on veut les métriques
            
        Returns:
            ProjectMetrics: Les métriques du projet
        """
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(project.__class__)
        
        metrics, created = ProjectMetrics.objects.get_or_create(
            content_type=content_type,
            object_id=project.id
        )
        return metrics
    
    @staticmethod
    def recalculate_project_metrics(project):
        """
        Recalcule toutes les métriques d'un projet à partir des données sources.
        
        Args:
            project: Le projet dont on veut recalculer les métriques
            
        Returns:
            ProjectMetrics: Les métriques du projet mises à jour
        """
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(project.__class__)
        
        # Récupérer les métriques du projet
        metrics, created = ProjectMetrics.objects.get_or_create(
            content_type=content_type,
            object_id=project.id
        )
        
        # Calculer les différentes métriques
        view_count = EventLog.objects.filter(
            event_type=EventLog.EventType.PROJECT_VIEW,
            content_type=content_type,
            object_id=project.id
        ).count()
        
        interest_count = ProjectInterest.objects.filter(project=project).count()
        
        favorite_count = ProjectFavorite.objects.filter(project=project).count()
        
        comment_count = EventLog.objects.filter(
            event_type=EventLog.EventType.PROJECT_COMMENT,
            content_type=content_type,
            object_id=project.id
        ).count()
        
        share_count = EventLog.objects.filter(
            event_type=EventLog.EventType.PROJECT_SHARE,
            content_type=content_type,
            object_id=project.id
        ).count()
        
        investments = Investment.objects.filter(project=project)
        investment_count = investments.count()
        total_investment_amount = investments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Mettre à jour les métriques
        with transaction.atomic():
            metrics.view_count = view_count
            metrics.interest_count = interest_count
            metrics.favorite_count = favorite_count
            metrics.comment_count = comment_count
            metrics.share_count = share_count
            metrics.investment_count = investment_count
            metrics.total_investment_amount = total_investment_amount
            
            # Calculer les taux de conversion
            metrics.update_conversion_rates()
            
            return metrics
    
    @staticmethod
    def get_period_metrics(start_date, end_date):
        """
        Récupère les métriques agrégées pour une période donnée.
        
        Args:
            start_date: Date de début de la période
            end_date: Date de fin de la période
            
        Returns:
            dict: Dictionnaire contenant les métriques agrégées
        """
        # Convertir en objets date si nécessaire
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Récupérer les métriques quotidiennes pour la période
        daily_metrics = DailyMetrics.objects.filter(date__range=(start_date, end_date))
        
        # Agréger les métriques
        aggregated = daily_metrics.aggregate(
            new_users=Sum('new_users_count'),
            active_users=Sum('active_users_count'),
            new_projects=Sum('new_projects_count'),
            published_projects=Sum('published_projects_count'),
            total_views=Sum('total_views_count'),
            total_interests=Sum('total_interests_count'),
            total_investment=Sum('total_investment_amount'),
            new_subscriptions=Sum('new_subscriptions_count'),
            subscription_revenue=Sum('subscription_revenue')
        )
        
        # Remplir avec des zéros si aucune donnée
        for key, value in aggregated.items():
            if value is None:
                aggregated[key] = 0
        
        # Ajouter des métriques calculées
        days_count = (end_date - start_date).days + 1
        
        aggregated['period_start'] = start_date
        aggregated['period_end'] = end_date
        aggregated['days_count'] = days_count
        
        # Métriques moyennes par jour
        aggregated['avg_new_users_per_day'] = aggregated['new_users'] / days_count if days_count > 0 else 0
        aggregated['avg_active_users_per_day'] = aggregated['active_users'] / days_count if days_count > 0 else 0
        aggregated['avg_new_projects_per_day'] = aggregated['new_projects'] / days_count if days_count > 0 else 0
        aggregated['avg_views_per_day'] = aggregated['total_views'] / days_count if days_count > 0 else 0
        
        # Taux de conversion
        aggregated['view_to_interest_rate'] = (aggregated['total_interests'] / aggregated['total_views'] * 100) if aggregated['total_views'] > 0 else 0
        
        return aggregated
    
    @staticmethod
    def get_top_projects(period_days=30, limit=10, metric='view_count'):
        """
        Récupère les projets les plus performants selon une métrique donnée.
        
        Args:
            period_days: Nombre de jours à considérer
            limit: Nombre maximum de projets à retourner
            metric: Métrique à utiliser pour le classement
            
        Returns:
            list: Liste des projets les plus performants avec leurs métriques
        """
        valid_metrics = ['view_count', 'interest_count', 'favorite_count', 
                        'investment_count', 'total_investment_amount']
        
        if metric not in valid_metrics:
            raise ValueError(f"Métrique invalide. Valeurs possibles: {', '.join(valid_metrics)}")
        
        # Calcul de la date de début de la période
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Récupérer les métriques de projet pour la période
        project_metrics = ProjectMetrics.objects.filter(
            updated_at__gte=start_date
        ).order_by(f'-{metric}')[:limit]
        
        # Construire le résultat
        result = []
        for pm in project_metrics:
            try:
                project = pm.project
                if project and hasattr(project, 'name'):
                    result.append({
                        'project_id': pm.object_id,
                        'project_name': project.name,
                        'view_count': pm.view_count,
                        'interest_count': pm.interest_count,
                        'favorite_count': pm.favorite_count,
                        'investment_count': pm.investment_count,
                        'total_investment_amount': pm.total_investment_amount,
                        'view_to_interest_rate': pm.view_to_interest_rate
                    })
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du projet {pm.object_id}: {str(e)}")
        
        return result 