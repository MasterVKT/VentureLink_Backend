"""
Tâches Celery pour les notifications.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationUserPreference,
    NotificationStatus, NotificationCategory, NotificationDeliveryMethod
)
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.fcm_service import FCMService
from apps.notifications.services.email_service import EmailNotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_async(self, notification_id: str):
    """
    Tâche asynchrone pour envoyer une notification.
    
    Args:
        notification_id: ID de la notification à envoyer
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Vérifier les préférences utilisateur
        user_prefs = NotificationUserPreference.objects.filter(
            user=notification.recipient
        ).first()
        
        if not user_prefs:
            # Créer des préférences par défaut si elles n'existent pas
            user_prefs = NotificationUserPreference.objects.create(
                user=notification.recipient
            )
        
        # Vérifier si l'utilisateur accepte cette catégorie
        if not user_prefs.is_category_enabled(notification.category):
            logger.info(f"Notification {notification_id} ignorée - catégorie désactivée")
            return
        
        delivery_methods = notification.get_delivery_methods_list()
        success_methods = []
        
        # Envoyer via chaque méthode activée
        for method in delivery_methods:
            try:
                if method == NotificationDeliveryMethod.PUSH and user_prefs.enable_push:
                    FCMService.send_push_notification(notification)
                    success_methods.append(method)
                    
                elif method == NotificationDeliveryMethod.EMAIL and user_prefs.enable_email:
                    EmailNotificationService.send_email_notification(notification)
                    success_methods.append(method)
                    
                elif method == NotificationDeliveryMethod.APP and user_prefs.enable_app:
                    # Notification in-app (déjà créée en base)
                    success_methods.append(method)
                    
            except Exception as e:
                logger.error(f"Erreur envoi notification {notification_id} via {method}: {e}")
        
        # Marquer comme livrée si au moins une méthode a réussi
        if success_methods:
            notification.delivered = True
            notification.save(update_fields=['delivered'])
            
        logger.info(f"Notification {notification_id} envoyée via: {success_methods}")
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur envoi notification {notification_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_bulk_notifications(self, user_ids: List[str], template_code: str, context: Dict):
    """
    Tâche pour envoyer des notifications en masse.
    
    Args:
        user_ids: Liste des IDs utilisateurs
        template_code: Code du template de notification
        context: Contexte pour le template
    """
    try:
        template = NotificationTemplate.objects.get(code=template_code, is_active=True)
        users = User.objects.filter(id__in=user_ids, is_active=True)
        
        notifications_created = []
        
        for user in users:
            try:
                notification = NotificationService.create_notification_from_template(
                    recipient=user,
                    template=template,
                    context=context
                )
                notifications_created.append(notification.id)
                
                # Envoyer immédiatement
                send_notification_async.delay(str(notification.id))
                
            except Exception as e:
                logger.error(f"Erreur création notification pour user {user.id}: {e}")
        
        logger.info(f"Notifications en masse créées: {len(notifications_created)}")
        return notifications_created
        
    except NotificationTemplate.DoesNotExist:
        logger.error(f"Template {template_code} introuvable")
    except Exception as exc:
        logger.error(f"Erreur notifications en masse: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def clean_old_notifications():
    """
    Tâche périodique pour nettoyer les anciennes notifications.
    """
    try:
        # Supprimer les notifications lues de plus de 30 jours
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_read_notifications = Notification.objects.filter(
            status=NotificationStatus.READ,
            read_at__lt=cutoff_date
        )
        
        count_read = old_read_notifications.count()
        old_read_notifications.delete()
        
        # Supprimer les notifications non lues de plus de 90 jours
        very_old_cutoff = timezone.now() - timedelta(days=90)
        
        very_old_notifications = Notification.objects.filter(
            created_at__lt=very_old_cutoff
        )
        
        count_very_old = very_old_notifications.count()
        very_old_notifications.delete()
        
        logger.info(f"Nettoyage notifications: {count_read} lues supprimées, {count_very_old} très anciennes supprimées")
        
        return {
            'old_read_deleted': count_read,
            'very_old_deleted': count_very_old
        }
        
    except Exception as e:
        logger.error(f"Erreur nettoyage notifications: {e}")
        raise


@shared_task
def send_digest_notifications():
    """
    Tâche périodique pour envoyer des notifications de résumé.
    """
    try:
        # Trouver les utilisateurs avec des notifications non lues
        users_with_unread = User.objects.filter(
            notifications__status=NotificationStatus.UNREAD,
            is_active=True
        ).distinct()
        
        digest_sent = 0
        
        for user in users_with_unread:
            try:
                # Vérifier les préférences utilisateur
                user_prefs = NotificationUserPreference.objects.filter(user=user).first()
                if not user_prefs or not user_prefs.enable_email:
                    continue
                
                # Compter les notifications non lues par catégorie
                unread_counts = {}
                for category in NotificationCategory:
                    count = user.notifications.filter(
                        status=NotificationStatus.UNREAD,
                        category=category.value
                    ).count()
                    if count > 0:
                        unread_counts[category.label] = count
                
                if unread_counts:
                    # Créer notification de résumé
                    total_unread = sum(unread_counts.values())
                    
                    context = {
                        'user_name': user.get_full_name() or user.email,
                        'total_unread': total_unread,
                        'categories': unread_counts
                    }
                    
                    notification = NotificationService.create_notification_from_template(
                        recipient=user,
                        template_code='DIGEST_NOTIFICATION',
                        context=context
                    )
                    
                    # Envoyer par email uniquement
                    EmailNotificationService.send_email_notification(notification)
                    digest_sent += 1
                    
            except Exception as e:
                logger.error(f"Erreur envoi digest pour user {user.id}: {e}")
        
        logger.info(f"Notifications de résumé envoyées: {digest_sent}")
        return {'digest_sent': digest_sent}
        
    except Exception as e:
        logger.error(f"Erreur envoi notifications de résumé: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def send_project_notification(self, project_id: str, notification_type: str, context: Dict):
    """
    Tâche pour envoyer des notifications liées aux projets.
    
    Args:
        project_id: ID du projet
        notification_type: Type de notification (NEW_INTEREST, STATUS_UPDATE, etc.)
        context: Contexte additionnel
    """
    try:
        from apps.projects.models import Project
        
        project = Project.objects.get(id=project_id)
        
        # Déterminer les destinataires selon le type
        recipients = []
        
        if notification_type == 'NEW_INTEREST':
            # Notifier le créateur du projet
            recipients = [project.creator]
            template_code = 'PROJECT_NEW_INTEREST'
            
        elif notification_type == 'STATUS_UPDATE':
            # Notifier tous les utilisateurs intéressés
            recipients = [interest.user for interest in project.interests.all()]
            template_code = 'PROJECT_STATUS_UPDATE'
            
        elif notification_type == 'NEW_UPDATE':
            # Notifier les followers du projet
            recipients = [fav.user for fav in project.favorites.all()]
            template_code = 'PROJECT_NEW_UPDATE'
        
        # Créer et envoyer les notifications
        for recipient in recipients:
            notification_context = {
                'project_title': project.title,
                'project_creator': project.creator.get_full_name(),
                **context
            }
            
            notification = NotificationService.create_notification_from_template(
                recipient=recipient,
                template_code=template_code,
                context=notification_context
            )
            
            # Envoyer immédiatement
            send_notification_async.delay(str(notification.id))
        
        logger.info(f"Notifications projet {project_id} envoyées à {len(recipients)} utilisateurs")
        
    except Project.DoesNotExist:
        logger.error(f"Projet {project_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur notifications projet {project_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_message_notification(self, message_id: str):
    """
    Tâche pour envoyer des notifications de nouveaux messages.
    
    Args:
        message_id: ID du message
    """
    try:
        from apps.messaging.models import Message
        
        message = Message.objects.get(id=message_id)
        conversation = message.conversation
        
        # Notifier tous les participants sauf l'expéditeur
        recipients = conversation.participants.exclude(id=message.sender.id)
        
        for recipient in recipients:
            # Vérifier si l'utilisateur a mis la conversation en sourdine
            participant = conversation.conversation_participants.filter(user=recipient).first()
            if participant and participant.muted_until and participant.muted_until > timezone.now():
                continue
            
            context = {
                'sender_name': message.sender.get_full_name() or message.sender.email,
                'conversation_title': str(conversation),
                'message_preview': message.content[:100] + '...' if len(message.content) > 100 else message.content
            }
            
            notification = NotificationService.create_notification_from_template(
                recipient=recipient,
                template_code='NEW_MESSAGE',
                context=context
            )
            
            # Envoyer immédiatement
            send_notification_async.delay(str(notification.id))
        
        logger.info(f"Notifications message {message_id} envoyées")
        
    except Message.DoesNotExist:
        logger.error(f"Message {message_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur notification message {message_id}: {exc}")
        raise self.retry(exc=exc, countdown=60) 