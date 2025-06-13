"""
Service pour l'envoi des notifications via Firebase Cloud Messaging.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Union
from firebase_admin import messaging
from django.conf import settings

from apps.core.utils.firebase import firebase_app
from apps.notifications.models import Notification, NotificationDeliveryMethod, NotificationStatus
from apps.users.models import User, DeviceToken

logger = logging.getLogger(__name__)

class FirebaseNotificationService:
    """
    Service pour l'envoi de notifications via Firebase Cloud Messaging.
    """
    
    @staticmethod
    def send_notification(
        notification: Notification,
        tokens: Optional[List[str]] = None
    ) -> bool:
        """
        Envoie une notification via Firebase Cloud Messaging.
        
        Args:
            notification: L'instance de notification à envoyer
            tokens: Liste optionnelle de tokens FCM. Si non fournie, les tokens de l'utilisateur seront utilisés.
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not firebase_app:
            logger.error("Firebase Admin SDK n'est pas initialisé. Impossible d'envoyer la notification.")
            return False
            
        # Vérifier que la notification doit être envoyée par FCM
        if NotificationDeliveryMethod.PUSH not in notification.get_delivery_methods():
            logger.debug(f"La notification {notification.id} n'est pas configurée pour être envoyée par FCM")
            return False
            
        # Si aucun token n'est fourni, récupérer les tokens de l'utilisateur
        if not tokens:
            tokens = DeviceToken.objects.filter(
                user=notification.recipient,
                is_active=True
            ).values_list('token', flat=True)
            
        if not tokens:
            logger.warning(f"Aucun token FCM actif trouvé pour l'utilisateur {notification.recipient.id}")
            return False
            
        # Préparer les données de la notification
        notification_data = {
            'id': str(notification.id),
            'title': notification.title,
            'body': notification.content,
            'category': notification.category,
            'priority': notification.priority,
            'created_at': notification.created_at.isoformat(),
            'action_url': notification.action_url or '',
        }
        
        # Ajouter des données sur l'objet lié si présent
        if notification.content_type and notification.object_id:
            notification_data.update({
                'content_type': notification.content_type.model,
                'object_id': notification.object_id,
            })
            
        # Créer le message FCM
        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=notification.title,
                body=notification.content,
                image=notification.icon_url if hasattr(notification, 'icon_url') else None,
            ),
            data={k: str(v) for k, v in notification_data.items()},  # FCM n'accepte que des chaînes de caractères
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#42B72A',
                    channel_id='general_notifications'
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=1,
                        sound='default',
                        content_available=True,
                    )
                ),
            ),
        )
        
        try:
            # Envoyer la notification
            response = messaging.send_multicast(message)
            
            # Mettre à jour la notification avec le statut d'envoi
            if response.success_count > 0:
                notification.delivery_status = 'delivered'
                notification.save(update_fields=['delivery_status'])
                logger.info(f"Notification {notification.id} envoyée avec succès à {response.success_count} appareils")
                return True
            else:
                logger.warning(f"Échec de l'envoi de la notification {notification.id}. Erreurs: {response.failure_count}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification FCM: {str(e)}")
            return False
    
    @staticmethod
    def send_data_message(
        user: User,
        data: Dict[str, Any],
        tokens: Optional[List[str]] = None
    ) -> bool:
        """
        Envoie un message de données silencieux via Firebase Cloud Messaging.
        
        Args:
            user: L'utilisateur destinataire
            data: Les données à envoyer
            tokens: Liste optionnelle de tokens FCM. Si non fournie, les tokens de l'utilisateur seront utilisés.
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not firebase_app:
            logger.error("Firebase Admin SDK n'est pas initialisé. Impossible d'envoyer le message.")
            return False
            
        # Si aucun token n'est fourni, récupérer les tokens de l'utilisateur
        if not tokens:
            tokens = DeviceToken.objects.filter(
                user=user,
                is_active=True
            ).values_list('token', flat=True)
            
        if not tokens:
            logger.warning(f"Aucun token FCM actif trouvé pour l'utilisateur {user.id}")
            return False
            
        # Convertir toutes les valeurs en chaînes pour FCM
        data_str = {k: str(v) for k, v in data.items()}
        
        # Créer le message FCM
        message = messaging.MulticastMessage(
            tokens=tokens,
            data=data_str,
            android=messaging.AndroidConfig(
                priority='normal',
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        content_available=True,
                    )
                ),
            ),
        )
        
        try:
            # Envoyer le message
            response = messaging.send_multicast(message)
            
            if response.success_count > 0:
                logger.info(f"Message de données envoyé avec succès à {response.success_count} appareils pour l'utilisateur {user.id}")
                return True
            else:
                logger.warning(f"Échec de l'envoi du message de données. Erreurs: {response.failure_count}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message FCM: {str(e)}")
            return False
    
    @staticmethod
    def send_topic_notification(
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envoie une notification à tous les appareils abonnés à un sujet.
        
        Args:
            topic: Le nom du sujet
            title: Le titre de la notification
            body: Le corps de la notification
            data: Les données supplémentaires à envoyer
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        if not firebase_app:
            logger.error("Firebase Admin SDK n'est pas initialisé. Impossible d'envoyer la notification.")
            return False
            
        # Convertir les données en chaînes pour FCM
        data_str = {k: str(v) for k, v in (data or {}).items()}
        
        # Créer le message FCM
        message = messaging.Message(
            topic=topic,
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data_str,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#42B72A',
                    channel_id='general_notifications'
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=1,
                        sound='default',
                    )
                ),
            ),
        )
        
        try:
            # Envoyer la notification
            response = messaging.send(message)
            logger.info(f"Notification envoyée avec succès au topic {topic}. Message ID: {response}")
            return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification au topic {topic}: {str(e)}")
            return False 