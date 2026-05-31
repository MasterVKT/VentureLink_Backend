"""
Signaux pour la mise à jour automatique des métriques.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from apps.projects.models import Project, ProjectInterest
from apps.investments.models import Investment
from apps.payments.models import Payment, UserSubscription
from apps.analytics.models import UserMetrics, ProjectMetrics, EventLog

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_metrics(sender, instance, created, **kwargs):
    """Crée un objet UserMetrics quand un nouvel utilisateur est créé."""
    if created:
        UserMetrics.objects.create(user=instance)
        
        # Enregistrer l'événement
        EventLog.objects.create(
            event_type=EventLog.EventType.USER_REGISTRATION,
            user=instance
        )


@receiver(post_save, sender=Project)
def update_project_metrics(sender, instance, created, **kwargs):
    """Met à jour les métriques de projet et d'utilisateur."""
    # Obtenir ou créer les métriques du projet
    content_type = ContentType.objects.get_for_model(Project)
    
    if created:
        # Créer les métriques du projet
        ProjectMetrics.objects.create(
            content_type=content_type,
            object_id=instance.id
        )
        
        # Mettre à jour les métriques de l'utilisateur
        if instance.creator:
            user_metrics, _ = UserMetrics.objects.get_or_create(user=instance.creator)
            user_metrics.projects_created_count += 1
            if instance.is_published:
                user_metrics.projects_published_count += 1
            user_metrics.save()
    else:
        # Si le projet vient d'être publié
        # FIXME: Tracker not configured for Project model
        # if instance.is_published and instance.tracker.has_changed('is_published'):
        #     # Mettre à jour les métriques de l'utilisateur
        #     if instance.creator:
        #         user_metrics, _ = UserMetrics.objects.get_or_create(user=instance.creator)
        #         user_metrics.projects_published_count += 1
        #         user_metrics.save()
        pass


@receiver(post_save, sender=ProjectInterest)
def update_interest_metrics(sender, instance, created, **kwargs):
    """Met à jour les métriques d'intérêt pour les projets."""
    if created:
        # Mettre à jour les métriques du projet
        content_type = ContentType.objects.get_for_model(Project)
        project_metrics, _ = ProjectMetrics.objects.get_or_create(
            content_type=content_type,
            object_id=instance.project.id
        )
        
        with transaction.atomic():
            project_metrics.interest_count += 1
            project_metrics.update_conversion_rates()
            project_metrics.save()
            
            # Mettre à jour les métriques de l'utilisateur propriétaire du projet
            if instance.project.creator:
                user_metrics, _ = UserMetrics.objects.get_or_create(user=instance.project.creator)
                user_metrics.total_project_interests += 1
                user_metrics.save()
        
        # Enregistrer l'événement
        EventLog.objects.create(
            event_type=EventLog.EventType.PROJECT_INTEREST,
            user=instance.user,
            content_type=content_type,
            object_id=instance.project.id,
            metadata={'interest_id': str(instance.id)}
        )


@receiver(post_save, sender=Investment)
def update_investment_metrics(sender, instance, created, **kwargs):
    """Met à jour les métriques d'investissement."""
    if created:
        # Mettre à jour les métriques du projet
        content_type = ContentType.objects.get_for_model(Project)
        project_metrics, _ = ProjectMetrics.objects.get_or_create(
            content_type=content_type,
            object_id=instance.project.id
        )
        
        with transaction.atomic():
            project_metrics.investment_count += 1
            project_metrics.total_investment_amount += instance.amount
            project_metrics.update_conversion_rates()
            project_metrics.save()
            
            # Mettre à jour les métriques de l'investisseur
            investor_metrics, _ = UserMetrics.objects.get_or_create(user=instance.investor)
            investor_metrics.investments_made_count += 1
            investor_metrics.total_investment_amount += instance.amount
            investor_metrics.save()
        
        # Enregistrer l'événement
        EventLog.objects.create(
            event_type=EventLog.EventType.INVESTMENT_MADE,
            user=instance.investor,
            content_type=content_type,
            object_id=instance.project.id,
            metadata={
                'investment_id': str(instance.id),
                'amount': float(instance.amount),
                'currency': instance.currency
            }
        )


@receiver(post_save, sender=Payment)
def update_payment_metrics(sender, instance, **kwargs):
    """Met à jour les métriques de paiement."""
    # Uniquement pour les paiements complétés
    if instance.status == Payment.PaymentStatus.COMPLETED:
        # Si c'est un paiement d'abonnement
        if instance.payment_type == Payment.PaymentType.SUBSCRIPTION:
            # Enregistrer l'événement
            EventLog.objects.create(
                event_type=EventLog.EventType.SUBSCRIPTION_STARTED,
                user=instance.user,
                metadata={
                    'payment_id': str(instance.id),
                    'amount': float(instance.amount),
                    'currency': instance.currency,
                    'subscription_plan': instance.metadata.get('plan_name', '')
                }
            )


@receiver(post_save, sender=UserSubscription)
def update_subscription_metrics(sender, instance, created, **kwargs):
    """Met à jour les métriques d'abonnement."""
    # Si l'abonnement vient d'être créé ou a changé de statut
    # FIXME: Tracker not configured for UserSubscription model
    # if created or instance.tracker.has_changed('status'):
    if created:
        if instance.status == 'ACTIVE':
            # Enregistrer l'événement
            if created: # or instance.tracker.previous('status') != 'ACTIVE':
                EventLog.objects.create(
                    event_type=EventLog.EventType.SUBSCRIPTION_STARTED,
                    user=instance.user,
                    metadata={
                        'subscription_id': str(instance.id),
                        'plan_name': instance.plan.name,
                        'start_date': instance.started_at.isoformat() if instance.started_at else None,
                        'end_date': instance.expires_at.isoformat() if instance.expires_at else None
                    }
                )
        # elif instance.status == 'CANCELLED' and instance.tracker.previous('status') == 'ACTIVE':
            # Enregistrer l'événement d'annulation
            EventLog.objects.create(
                event_type=EventLog.EventType.SUBSCRIPTION_CANCELED,
                user=instance.user,
                metadata={
                    'subscription_id': str(instance.id),
                    'plan_name': instance.plan.name,
                    'cancellation_date': timezone.now().isoformat()
                }
            )


def log_project_view(project, user=None, ip_address=None, user_agent=None):
    """
    Enregistre une vue de projet et met à jour les métriques associées.
    
    Args:
        project: Le projet vu
        user: L'utilisateur qui a vu le projet (optionnel)
        ip_address: L'adresse IP de l'utilisateur (optionnel)
        user_agent: Le user agent de l'utilisateur (optionnel)
    """
    # Mettre à jour les métriques du projet
    content_type = ContentType.objects.get_for_model(Project)
    project_metrics, _ = ProjectMetrics.objects.get_or_create(
        content_type=content_type,
        object_id=project.id
    )
    
    with transaction.atomic():
        project_metrics.view_count += 1
        project_metrics.update_conversion_rates()
        project_metrics.save()
        
        # Mettre à jour les métriques de l'utilisateur propriétaire du projet
        if project.creator:
            user_metrics, _ = UserMetrics.objects.get_or_create(user=project.creator)
            user_metrics.total_project_views += 1
            user_metrics.save()
    
    # Enregistrer l'événement
    EventLog.objects.create(
        event_type=EventLog.EventType.PROJECT_VIEW,
        user=user,
        content_type=content_type,
        object_id=project.id,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_login(user, ip_address=None, user_agent=None):
    """
    Enregistre une connexion utilisateur et met à jour les métriques associées.
    
    Args:
        user: L'utilisateur qui s'est connecté
        ip_address: L'adresse IP de l'utilisateur (optionnel)
        user_agent: Le user agent de l'utilisateur (optionnel)
    """
    # Mettre à jour les métriques de l'utilisateur
    user_metrics, _ = UserMetrics.objects.get_or_create(user=user)
    user_metrics.login_count += 1
    user_metrics.last_login = timezone.now()
    user_metrics.save()
    
    # Enregistrer l'événement
    EventLog.objects.create(
        event_type=EventLog.EventType.USER_LOGIN,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    ) 