"""
Vues API pour les métriques et statistiques.
"""
import logging
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from apps.core.permissions import IsAdminUser
from apps.projects.models import Project
from apps.analytics.services.metrics_service import MetricsService
from apps.core.services.currency_service import CurrencyService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_metrics_view(request):
    """
    Récupère les métriques de l'utilisateur connecté.
    
    Cette vue renvoie un résumé des métriques de l'utilisateur,
    comme le nombre de projets créés, le nombre de vues sur ses projets, etc.
    """
    try:
        # Récupérer les métriques de l'utilisateur
        metrics = MetricsService.get_user_metrics(request.user)
        
        # Préparer la réponse
        currency = request.GET.get('currency', 'EUR')
        
        # Convertir les montants dans la devise demandée
        total_investment_amount = metrics.total_investment_amount
        if currency != 'EUR':
            total_investment_amount = CurrencyService.convert_amount(
                amount=total_investment_amount,
                from_currency='EUR',
                to_currency=currency
            )
        
        data = {
            'projects_created_count': metrics.projects_created_count,
            'projects_published_count': metrics.projects_published_count,
            'total_project_views': metrics.total_project_views,
            'total_project_interests': metrics.total_project_interests,
            'total_comments_received': metrics.total_comments_received,
            'investments_made_count': metrics.investments_made_count,
            'total_investment_amount': total_investment_amount,
            'total_investment_currency': currency,
            'messages_sent_count': metrics.messages_sent_count,
            'messages_received_count': metrics.messages_received_count,
            'login_count': metrics.login_count,
            'last_login': metrics.last_login,
        }
        
        return Response(data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques utilisateur: {str(e)}")
        return Response(
            {'error': 'Une erreur est survenue lors de la récupération des métriques'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_metrics_view(request, project_id):
    """
    Récupère les métriques d'un projet spécifique.
    
    Cette vue renvoie un résumé des métriques du projet,
    comme le nombre de vues, le nombre d'intérêts exprimés, etc.
    """
    try:
        # Récupérer le projet
        project = get_object_or_404(Project, id=project_id)
        
        # Vérifier que l'utilisateur a le droit de voir les métriques
        if not (request.user.is_staff or request.user == project.creator):
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à voir ces métriques'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les métriques du projet
        metrics = MetricsService.get_project_metrics(project)
        
        # Préparer la réponse
        currency = request.GET.get('currency', 'EUR')
        
        # Convertir les montants dans la devise demandée
        total_investment_amount = metrics.total_investment_amount
        if currency != 'EUR':
            total_investment_amount = CurrencyService.convert_amount(
                amount=total_investment_amount,
                from_currency='EUR',
                to_currency=currency
            )
        
        data = {
            'project_id': str(project.id),
            'project_name': project.name,
            'view_count': metrics.view_count,
            'interest_count': metrics.interest_count,
            'favorite_count': metrics.favorite_count,
            'comment_count': metrics.comment_count,
            'share_count': metrics.share_count,
            'investment_count': metrics.investment_count,
            'total_investment_amount': total_investment_amount,
            'total_investment_currency': currency,
            'view_to_interest_rate': metrics.view_to_interest_rate,
            'interest_to_investment_rate': metrics.interest_to_investment_rate,
        }
        
        return Response(data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques du projet: {str(e)}")
        return Response(
            {'error': 'Une erreur est survenue lors de la récupération des métriques'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DashboardMetricsView(APIView):
    """
    Vue pour les métriques du tableau de bord administrateur.
    
    Cette vue renvoie les métriques globales de la plateforme
    pour une période donnée.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère les métriques pour le tableau de bord."""
        try:
            # Récupérer les paramètres de période
            period = request.GET.get('period', 'week')
            end_date = timezone.now().date()
            
            # Déterminer la date de début en fonction de la période
            if period == 'day':
                start_date = end_date
            elif period == 'week':
                start_date = end_date - timedelta(days=6)  # 7 jours incluant aujourd'hui
            elif period == 'month':
                start_date = end_date - timedelta(days=29)  # 30 jours incluant aujourd'hui
            elif period == 'year':
                start_date = end_date - timedelta(days=364)  # 365 jours incluant aujourd'hui
            elif period == 'custom':
                # Format attendu: YYYY-MM-DD
                try:
                    start_date_str = request.GET.get('start_date')
                    if not start_date_str:
                        return Response(
                            {'error': 'La date de début est requise pour une période personnalisée'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Format de date invalide. Utilisez le format YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Période invalide. Valeurs possibles: day, week, month, year, custom'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer les métriques pour la période
            metrics = MetricsService.get_period_metrics(start_date, end_date)
            
            # Récupérer la devise demandée
            currency = request.GET.get('currency', 'EUR')
            
            # Convertir les montants si nécessaire
            if currency != 'EUR':
                metrics['total_investment'] = CurrencyService.convert_amount(
                    amount=metrics['total_investment'],
                    from_currency='EUR',
                    to_currency=currency
                )
                metrics['subscription_revenue'] = CurrencyService.convert_amount(
                    amount=metrics['subscription_revenue'],
                    from_currency='EUR',
                    to_currency=currency
                )
            
            # Ajouter la devise à la réponse
            metrics['currency'] = currency
            
            return Response(metrics)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques du tableau de bord: {str(e)}")
            return Response(
                {'error': 'Une erreur est survenue lors de la récupération des métriques'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopProjectsView(APIView):
    """
    Vue pour récupérer les projets les plus performants.
    
    Cette vue renvoie une liste des projets les plus performants
    selon une métrique donnée.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère les projets les plus performants."""
        try:
            # Récupérer les paramètres
            metric = request.GET.get('metric', 'view_count')
            limit = int(request.GET.get('limit', 10))
            period_days = int(request.GET.get('period_days', 30))
            
            # Valider les paramètres
            valid_metrics = ['view_count', 'interest_count', 'favorite_count', 
                            'investment_count', 'total_investment_amount']
            if metric not in valid_metrics:
                return Response(
                    {'error': f"Métrique invalide. Valeurs possibles: {', '.join(valid_metrics)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if limit < 1 or limit > 50:
                return Response(
                    {'error': 'La limite doit être comprise entre 1 et 50'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if period_days < 1 or period_days > 365:
                return Response(
                    {'error': 'La période doit être comprise entre 1 et 365 jours'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer les projets
            top_projects = MetricsService.get_top_projects(
                period_days=period_days,
                limit=limit,
                metric=metric
            )
            
            # Récupérer la devise demandée
            currency = request.GET.get('currency', 'EUR')
            
            # Convertir les montants si nécessaire
            if currency != 'EUR':
                for project in top_projects:
                    project['total_investment_amount'] = CurrencyService.convert_amount(
                        amount=project['total_investment_amount'],
                        from_currency='EUR',
                        to_currency=currency
                    )
            
            # Ajouter la devise à la réponse
            result = {
                'projects': top_projects,
                'currency': currency,
                'metric': metric,
                'period_days': period_days
            }
            
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets les plus performants: {str(e)}")
            return Response(
                {'error': 'Une erreur est survenue lors de la récupération des projets'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Alias pour les fonctions de vue
UserMetricsView = user_metrics_view
ProjectMetricsView = project_metrics_view 