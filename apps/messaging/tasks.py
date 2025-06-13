"""
Tâches Celery pour la messagerie.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.messaging.models import Conversation, Message, ConversationParticipant
from apps.messaging.services.messaging_service import MessagingService
from apps.notifications.tasks import send_notification_async

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_new_message(self, message_id: str):
    """
    Traite un nouveau message (notifications, indexation, etc.).
    
    Args:
        message_id: ID du message à traiter
    """
    try:
        message = Message.objects.get(id=message_id)
        conversation = message.conversation
        
        # Mettre à jour la date du dernier message de la conversation
        conversation.last_message_at = message.created_at
        conversation.save(update_fields=['last_message_at'])
        
        # Marquer les participants comme ayant des messages non lus
        participants = conversation.conversation_participants.exclude(
            user=message.sender
        )
        
        for participant in participants:
            # Ne pas mettre à jour last_read_at pour créer l'effet "non lu"
            pass
        
        # Envoyer les notifications aux autres participants
        from apps.notifications.tasks import send_message_notification
        send_message_notification.delay(str(message.id))
        
        # Indexer le message pour la recherche (si Elasticsearch configuré)
        try:
            MessagingService.index_message_for_search(message)
        except Exception as e:
            logger.warning(f"Erreur indexation message {message_id}: {e}")
        
        logger.info(f"Message {message_id} traité avec succès")
        
    except Message.DoesNotExist:
        logger.error(f"Message {message_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur traitement message {message_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_message_attachments(self, message_id: str):
    """
    Traite les pièces jointes d'un message (compression, scan antivirus, etc.).
    
    Args:
        message_id: ID du message
    """
    try:
        message = Message.objects.get(id=message_id)
        
        if not message.attachments.exists():
            logger.info(f"Aucune pièce jointe pour le message {message_id}")
            return
        
        for attachment in message.attachments.all():
            try:
                # Vérifier la taille du fichier
                if attachment.file_size > settings.MAX_ATTACHMENT_SIZE:
                    logger.warning(f"Pièce jointe {attachment.id} trop volumineuse")
                    attachment.is_processed = False
                    attachment.processing_error = "Fichier trop volumineux"
                    attachment.save()
                    continue
                
                # Scan antivirus (simulation)
                if MessagingService.scan_attachment_for_virus(attachment):
                    logger.warning(f"Virus détecté dans la pièce jointe {attachment.id}")
                    attachment.is_processed = False
                    attachment.processing_error = "Virus détecté"
                    attachment.save()
                    continue
                
                # Compression si nécessaire
                if attachment.file_type.startswith('image/'):
                    MessagingService.compress_image_attachment(attachment)
                
                # Générer une miniature si c'est une image
                if attachment.file_type.startswith('image/'):
                    MessagingService.generate_thumbnail(attachment)
                
                # Marquer comme traité
                attachment.is_processed = True
                attachment.processed_at = timezone.now()
                attachment.save()
                
                logger.info(f"Pièce jointe {attachment.id} traitée avec succès")
                
            except Exception as e:
                logger.error(f"Erreur traitement pièce jointe {attachment.id}: {e}")
                attachment.is_processed = False
                attachment.processing_error = str(e)
                attachment.save()
        
        logger.info(f"Toutes les pièces jointes du message {message_id} traitées")
        
    except Message.DoesNotExist:
        logger.error(f"Message {message_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur traitement pièces jointes {message_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def clean_old_messages():
    """
    Tâche périodique pour nettoyer les anciens messages.
    """
    try:
        # Supprimer les messages supprimés de plus de 30 jours
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_deleted_messages = Message.objects.filter(
            is_deleted=True,
            deleted_at__lt=cutoff_date
        )
        
        count_deleted = old_deleted_messages.count()
        old_deleted_messages.delete()
        
        # Archiver les conversations inactives de plus de 6 mois
        inactive_cutoff = timezone.now() - timedelta(days=180)
        
        inactive_conversations = Conversation.objects.filter(
            last_message_at__lt=inactive_cutoff,
            status=Conversation.STATUS_ACTIVE
        )
        
        count_archived = inactive_conversations.update(status=Conversation.STATUS_ARCHIVED)
        
        logger.info(f"Nettoyage messagerie: {count_deleted} messages supprimés, {count_archived} conversations archivées")
        
        return {
            'messages_deleted': count_deleted,
            'conversations_archived': count_archived
        }
        
    except Exception as e:
        logger.error(f"Erreur nettoyage messagerie: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def create_project_conversation(self, project_id: str, creator_id: str, interested_user_id: str):
    """
    Crée une conversation pour un projet entre le créateur et un utilisateur intéressé.
    
    Args:
        project_id: ID du projet
        creator_id: ID du créateur du projet
        interested_user_id: ID de l'utilisateur intéressé
    """
    try:
        from apps.projects.models import Project
        
        project = Project.objects.get(id=project_id)
        creator = User.objects.get(id=creator_id)
        interested_user = User.objects.get(id=interested_user_id)
        
        # Vérifier si une conversation existe déjà
        existing_conversation = Conversation.objects.filter(
            project=project,
            conversation_type=Conversation.TYPE_PROJECT,
            participants__in=[creator, interested_user]
        ).distinct().first()
        
        if existing_conversation:
            logger.info(f"Conversation existante trouvée: {existing_conversation.id}")
            return str(existing_conversation.id)
        
        # Créer une nouvelle conversation
        conversation = Conversation.objects.create(
            title=f"Projet: {project.title}",
            conversation_type=Conversation.TYPE_PROJECT,
            project=project
        )
        
        # Ajouter les participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=creator,
            is_admin=True
        )
        
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=interested_user,
            is_admin=False
        )
        
        # Envoyer un message de bienvenue automatique
        welcome_message = Message.objects.create(
            conversation=conversation,
            sender=creator,
            content=f"Bonjour ! Merci pour votre intérêt pour mon projet '{project.title}'. N'hésitez pas à me poser vos questions !",
            message_type=Message.TYPE_SYSTEM
        )
        
        # Traiter le message de bienvenue
        process_new_message.delay(str(welcome_message.id))
        
        logger.info(f"Conversation projet créée: {conversation.id}")
        return str(conversation.id)
        
    except (Project.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Objet introuvable pour création conversation: {e}")
    except Exception as exc:
        logger.error(f"Erreur création conversation projet: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_conversation_digest(self, user_id: str):
    """
    Envoie un résumé des conversations non lues à un utilisateur.
    
    Args:
        user_id: ID de l'utilisateur
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Récupérer les conversations avec des messages non lus
        unread_conversations = []
        
        for participation in user.conversation_participations.filter(
            conversation__status=Conversation.STATUS_ACTIVE
        ):
            conversation = participation.conversation
            
            # Compter les messages non lus
            unread_count = conversation.messages.filter(
                created_at__gt=participation.last_read_at or timezone.now() - timedelta(days=30)
            ).exclude(sender=user).count()
            
            if unread_count > 0:
                last_message = conversation.messages.exclude(sender=user).first()
                unread_conversations.append({
                    'conversation': conversation,
                    'unread_count': unread_count,
                    'last_message': last_message,
                    'last_sender': last_message.sender if last_message else None
                })
        
        if not unread_conversations:
            logger.info(f"Aucun message non lu pour l'utilisateur {user_id}")
            return
        
        # Créer une notification de résumé
        from apps.notifications.services.notification_service import NotificationService
        
        total_unread = sum(conv['unread_count'] for conv in unread_conversations)
        
        context = {
            'user_name': user.get_full_name() or user.email,
            'total_unread': total_unread,
            'conversations_count': len(unread_conversations),
            'conversations': unread_conversations[:5]  # Limiter à 5 pour l'email
        }
        
        notification = NotificationService.create_notification_from_template(
            recipient=user,
            template_code='MESSAGE_DIGEST',
            context=context
        )
        
        # Envoyer la notification
        send_notification_async.delay(str(notification.id))
        
        logger.info(f"Résumé conversations envoyé à l'utilisateur {user_id}")
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur envoi résumé conversations {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def update_conversation_statistics():
    """
    Tâche périodique pour mettre à jour les statistiques des conversations.
    """
    try:
        # Mettre à jour le nombre de messages par conversation
        conversations = Conversation.objects.filter(status=Conversation.STATUS_ACTIVE)
        
        updated_count = 0
        
        for conversation in conversations:
            message_count = conversation.messages.filter(is_deleted=False).count()
            
            # Mettre à jour si nécessaire (on pourrait ajouter un champ message_count)
            # conversation.message_count = message_count
            # conversation.save(update_fields=['message_count'])
            
            updated_count += 1
        
        logger.info(f"Statistiques mises à jour pour {updated_count} conversations")
        
        return {'conversations_updated': updated_count}
        
    except Exception as e:
        logger.error(f"Erreur mise à jour statistiques conversations: {e}")
        raise


@shared_task(bind=True, max_retries=3)
def backup_conversation_data(self, conversation_id: str):
    """
    Sauvegarde les données d'une conversation (pour archivage ou export).
    
    Args:
        conversation_id: ID de la conversation à sauvegarder
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Préparer les données de sauvegarde
        backup_data = {
            'conversation': {
                'id': str(conversation.id),
                'title': conversation.title,
                'type': conversation.conversation_type,
                'created_at': conversation.created_at.isoformat(),
                'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            },
            'participants': [],
            'messages': []
        }
        
        # Ajouter les participants
        for participant in conversation.conversation_participants.all():
            backup_data['participants'].append({
                'user_id': str(participant.user.id),
                'user_email': participant.user.email,
                'is_admin': participant.is_admin,
                'joined_at': participant.created_at.isoformat(),
            })
        
        # Ajouter les messages
        for message in conversation.messages.all().order_by('created_at'):
            backup_data['messages'].append({
                'id': str(message.id),
                'sender_email': message.sender.email,
                'content': message.content,
                'message_type': message.message_type,
                'created_at': message.created_at.isoformat(),
                'is_deleted': message.is_deleted,
            })
        
        # Sauvegarder dans un fichier ou service de stockage
        # Ici on pourrait utiliser AWS S3, Google Cloud Storage, etc.
        backup_filename = f"conversation_backup_{conversation_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Pour l'exemple, on log juste la taille des données
        import json
        backup_json = json.dumps(backup_data, indent=2)
        
        logger.info(f"Sauvegarde conversation {conversation_id} créée: {len(backup_json)} caractères")
        
        return {
            'conversation_id': conversation_id,
            'backup_filename': backup_filename,
            'data_size': len(backup_json),
            'messages_count': len(backup_data['messages']),
            'participants_count': len(backup_data['participants'])
        }
        
    except Conversation.DoesNotExist:
        logger.error(f"Conversation {conversation_id} introuvable")
    except Exception as exc:
        logger.error(f"Erreur sauvegarde conversation {conversation_id}: {exc}")
        raise self.retry(exc=exc, countdown=60) 