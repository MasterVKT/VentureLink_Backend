"""
Tâches Celery pour les analytics et métriques système.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate, TruncHour

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def update_daily_analytics():
    """
    Tâche périodique pour mettre à jour les analytics quotidiennes.
    """
    try:
        from apps.projects.models import Project, ProjectInterest, ProjectFavorite
        from apps.messaging.models import Message, Conversation
        from apps.notifications.models import Notification
        from apps.users.models import UserProfile
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Métriques utilisateurs
        total_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(
            date_joined__date=today
        ).count()
        active_users_today = User.objects.filter(
            last_login__date=today
        ).count()
        
        # Métriques projets
        total_projects = Project.objects.filter(
            status__in=['PUBLISHED', 'FUNDED']
        ).count()
        new_projects_today = Project.objects.filter(
            created_at__date=today
        ).count()
        
        # Métriques interactions
        new_interests_today = ProjectInterest.objects.filter(
            created_at__date=today
        ).count()
        new_favorites_today = ProjectFavorite.objects.filter(
            created_at__date=today
        ).count()
        
        # Métriques messagerie
        new_messages_today = Message.objects.filter(
            created_at__date=today,
            is_deleted=False
        ).count()
        new_conversations_today = Conversation.objects.filter(
            created_at__date=today
        ).count()
        
        # Métriques notifications
        notifications_sent_today = Notification.objects.filter(
            created_at__date=today,
            delivered=True
        ).count()
        
        analytics_data = {
            'date': today.isoformat(),
            'users': {
                'total': total_users,
                'new_today': new_users_today,
                'active_today': active_users_today,
            },
            'projects': {
                'total': total_projects,
                'new_today': new_projects_today,
            },
            'interactions': {
                'interests_today': new_interests_today,
                'favorites_today': new_favorites_today,
            },
            'messaging': {
                'messages_today': new_messages_today,
                'conversations_today': new_conversations_today,
            },
            'notifications': {
                'sent_today': notifications_sent_today,
            }
        }
        
        # Sauvegarder les métriques (ici on pourrait utiliser un modèle DailyMetrics)
        logger.info(f"Analytics quotidiennes calculées: {analytics_data}")
        
        # Envoyer à un service d'analytics externe si configuré
        if hasattr(settings, 'ANALYTICS_WEBHOOK_URL'):
            send_analytics_to_external_service.delay(analytics_data)
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Erreur calcul analytics quotidiennes: {e}")
        raise


@shared_task
def generate_user_engagement_report():
    """
    Génère un rapport d'engagement des utilisateurs.
    """
    try:
        from apps.projects.models import Project, ProjectInterest, ProjectFavorite
        from apps.messaging.models import Message
        
        # Période d'analyse (30 derniers jours)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Utilisateurs actifs par jour
        daily_active_users = User.objects.filter(
            last_login__gte=start_date
        ).extra(
            select={'day': 'date(last_login)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Projets créés par jour
        daily_projects = Project.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Interactions par jour
        daily_interactions = ProjectInterest.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Messages par jour
        daily_messages = Message.objects.filter(
            created_at__gte=start_date,
            is_deleted=False
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Top utilisateurs par activité
        top_users = User.objects.filter(
            is_active=True
        ).annotate(
            projects_count=Count('created_projects'),
            interests_count=Count('project_interests'),
            messages_count=Count('sent_messages')
        ).order_by('-projects_count', '-interests_count', '-messages_count')[:10]
        
        report_data = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'daily_active_users': list(daily_active_users),
            'daily_projects': list(daily_projects),
            'daily_interactions': list(daily_interactions),
            'daily_messages': list(daily_messages),
            'top_users': [
                {
                    'user_id': str(user.id),
                    'email': user.email,
                    'projects_count': user.projects_count,
                    'interests_count': user.interests_count,
                    'messages_count': user.messages_count,
                }
                for user in top_users
            ]
        }
        
        logger.info(f"Rapport d'engagement généré pour {len(top_users)} utilisateurs")
        
        return report_data
        
    except Exception as e:
        logger.error(f"Erreur génération rapport d'engagement: {e}")
        raise


@shared_task
def calculate_project_success_metrics():
    """
    Calcule les métriques de succès des projets.
    """
    try:
        from apps.projects.models import Project, ProjectInterest
        from apps.investments.models import Investment
        
        # Projets par statut
        project_stats = Project.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Taux de conversion intérêt -> investissement
        projects_with_interests = Project.objects.annotate(
            interests_count=Count('interests'),
            investments_count=Count('investments')
        ).filter(interests_count__gt=0)
        
        conversion_rates = []
        for project in projects_with_interests:
            if project.interests_count > 0:
                rate = (project.investments_count / project.interests_count) * 100
                conversion_rates.append({
                    'project_id': str(project.id),
                    'title': project.title,
                    'interests': project.interests_count,
                    'investments': project.investments_count,
                    'conversion_rate': round(rate, 2)
                })
        
        # Moyenne des taux de conversion
        avg_conversion_rate = sum(p['conversion_rate'] for p in conversion_rates) / len(conversion_rates) if conversion_rates else 0
        
        # Projets les plus populaires (par intérêts)
        popular_projects = Project.objects.annotate(
            interests_count=Count('interests')
        ).filter(interests_count__gt=0).order_by('-interests_count')[:10]
        
        # Temps moyen pour recevoir le premier intérêt
        projects_with_first_interest = []
        for project in Project.objects.filter(interests__isnull=False).distinct():
            first_interest = project.interests.order_by('created_at').first()
            if first_interest:
                time_to_first_interest = (first_interest.created_at - project.created_at).total_seconds() / 3600  # en heures
                projects_with_first_interest.append(time_to_first_interest)
        
        avg_time_to_first_interest = sum(projects_with_first_interest) / len(projects_with_first_interest) if projects_with_first_interest else 0
        
        metrics_data = {
            'project_stats': list(project_stats),
            'conversion_metrics': {
                'average_conversion_rate': round(avg_conversion_rate, 2),
                'projects_analyzed': len(conversion_rates),
                'top_converting_projects': sorted(conversion_rates, key=lambda x: x['conversion_rate'], reverse=True)[:5]
            },
            'popularity_metrics': {
                'average_time_to_first_interest_hours': round(avg_time_to_first_interest, 2),
                'most_popular_projects': [
                    {
                        'project_id': str(p.id),
                        'title': p.title,
                        'interests_count': p.interests_count
                    }
                    for p in popular_projects
                ]
            }
        }
        
        logger.info(f"Métriques de succès calculées pour {len(conversion_rates)} projets")
        
        return metrics_data
        
    except Exception as e:
        logger.error(f"Erreur calcul métriques de succès: {e}")
        raise


@shared_task
def generate_financial_analytics():
    """
    Génère les analytics financières.
    """
    try:
        from apps.investments.models import Investment
        from apps.payments.models import Payment
        
        # Période d'analyse (30 derniers jours)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Investissements par jour
        daily_investments = Investment.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('day')
        
        # Paiements par statut
        payment_stats = Payment.objects.filter(
            created_at__gte=start_date
        ).values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Montants par devise
        currency_stats = Investment.objects.filter(
            created_at__gte=start_date
        ).values('currency').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Top investisseurs
        top_investors = User.objects.annotate(
            investments_count=Count('investments'),
            total_invested=Sum('investments__amount')
        ).filter(
            investments_count__gt=0
        ).order_by('-total_invested')[:10]
        
        # Projets les plus financés
        top_funded_projects = Project.objects.annotate(
            total_funding=Sum('investments__amount'),
            investors_count=Count('investments__investor', distinct=True)
        ).filter(
            total_funding__gt=0
        ).order_by('-total_funding')[:10]
        
        financial_data = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'daily_investments': list(daily_investments),
            'payment_stats': list(payment_stats),
            'currency_stats': list(currency_stats),
            'top_investors': [
                {
                    'user_id': str(user.id),
                    'email': user.email,
                    'investments_count': user.investments_count,
                    'total_invested': float(user.total_invested or 0)
                }
                for user in top_investors
            ],
            'top_funded_projects': [
                {
                    'project_id': str(project.id),
                    'title': project.title,
                    'total_funding': float(project.total_funding or 0),
                    'investors_count': project.investors_count
                }
                for project in top_funded_projects
            ]
        }
        
        logger.info(f"Analytics financières générées")
        
        return financial_data
        
    except Exception as e:
        logger.error(f"Erreur génération analytics financières: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def send_analytics_to_external_service(self, analytics_data: Dict):
    """
    Envoie les données d'analytics à un service externe.
    
    Args:
        analytics_data: Données d'analytics à envoyer
    """
    try:
        import requests
        
        webhook_url = getattr(settings, 'ANALYTICS_WEBHOOK_URL', None)
        if not webhook_url:
            logger.warning("ANALYTICS_WEBHOOK_URL non configuré")
            return
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {getattr(settings, 'ANALYTICS_API_KEY', '')}"
        }
        
        response = requests.post(
            webhook_url,
            json=analytics_data,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info(f"Analytics envoyées au service externe: {response.status_code}")
        
    except requests.RequestException as e:
        logger.error(f"Erreur envoi analytics au service externe: {e}")
        raise self.retry(exc=e, countdown=60)
    except Exception as exc:
        logger.error(f"Erreur générale envoi analytics: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_old_analytics_data():
    """
    Nettoie les anciennes données d'analytics.
    """
    try:
        # Supprimer les données de plus de 1 an
        cutoff_date = timezone.now() - timedelta(days=365)
        
        # Ici on supprimerait les anciens enregistrements de métriques
        # si on avait des modèles DailyMetrics, HourlyMetrics, etc.
        
        logger.info(f"Nettoyage des données d'analytics antérieures au {cutoff_date}")
        
        return {'cutoff_date': cutoff_date.isoformat()}
        
    except Exception as e:
        logger.error(f"Erreur nettoyage données analytics: {e}")
        raise


@shared_task
def generate_weekly_summary_report():
    """
    Génère un rapport de résumé hebdomadaire.
    """
    try:
        # Période d'analyse (7 derniers jours)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Collecter toutes les métriques
        user_metrics = update_daily_analytics.delay().get()
        engagement_metrics = generate_user_engagement_report.delay().get()
        project_metrics = calculate_project_success_metrics.delay().get()
        financial_metrics = generate_financial_analytics.delay().get()
        
        summary_report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'summary': {
                'total_users': user_metrics['users']['total'],
                'new_users_week': user_metrics['users']['new_today'] * 7,  # Approximation
                'total_projects': user_metrics['projects']['total'],
                'avg_conversion_rate': project_metrics['conversion_metrics']['average_conversion_rate'],
            },
            'detailed_metrics': {
                'users': user_metrics,
                'engagement': engagement_metrics,
                'projects': project_metrics,
                'financial': financial_metrics,
            }
        }
        
        logger.info("Rapport de résumé hebdomadaire généré")
        
        # Envoyer le rapport par email aux administrateurs
        if hasattr(settings, 'ADMIN_EMAILS'):
            send_weekly_report_email.delay(summary_report)
        
        return summary_report
        
    except Exception as e:
        logger.error(f"Erreur génération rapport hebdomadaire: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def send_weekly_report_email(self, report_data: Dict):
    """
    Envoie le rapport hebdomadaire par email aux administrateurs.
    
    Args:
        report_data: Données du rapport
    """
    try:
        from apps.notifications.services.email_service import EmailNotificationService
        
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        if not admin_emails:
            logger.warning("ADMIN_EMAILS non configuré")
            return
        
        subject = f"Rapport hebdomadaire VentureLink - {report_data['period']['start']} à {report_data['period']['end']}"
        
        context = {
            'report': report_data,
            'period_start': report_data['period']['start'],
            'period_end': report_data['period']['end'],
        }
        
        result = EmailNotificationService.send_bulk_email_notification(
            recipients=admin_emails,
            subject=subject,
            template_name='weekly_report',
            context=context
        )
        
        logger.info(f"Rapport hebdomadaire envoyé à {result['success']} administrateurs")
        
    except Exception as exc:
        logger.error(f"Erreur envoi rapport hebdomadaire: {exc}")
        raise self.retry(exc=exc, countdown=60) 