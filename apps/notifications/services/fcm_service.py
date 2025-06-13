"""
Service Firebase Cloud Messaging pour les notifications push.
"""
import logging
from typing import Dict, List, Optional

from django.conf import settings
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from apps.notifications.models import Notification
from apps.users.models import DeviceToken

logger = logging.getLogger(__name__)


class FCMService:
    """
    Service pour envoyer des notifications push via Firebase Cloud Messaging.
    """
    
    @staticmethod
    def send_push_notification(notification: Notification) -> bool:
        """
        Envoie une notification push à un utilisateur.
        
        Args:
            notification: Instance de notification à envoyer
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        try:
            # Récupérer les tokens de l'utilisateur
            device_tokens = DeviceToken.objects.filter(
                user=notification.recipient,
                is_active=True
            ).values_list('token', flat=True)
            
            if not device_tokens:
                logger.warning(f"Aucun token FCM pour l'utilisateur {notification.recipient.id}")
                return False
            
            # Préparer le message
            message_data = FCMService._prepare_message_data(notification)
            
            # Envoyer à tous les appareils de l'utilisateur
            success_count = 0
            invalid_tokens = []
            
            for token in device_tokens:
                try:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=notification.title,
                            body=notification.content,
                            image=message_data.get('image_url')
                        ),
                        data=message_data,
                        token=token,
                        android=messaging.AndroidConfig(
                            priority='high',
                            notification=messaging.AndroidNotification(
                                icon=notification.icon or 'ic_notification',
                                color='#1976D2',  # Couleur VentureLink
                                sound='default',
                                click_action='FLUTTER_NOTIFICATION_CLICK'
                            )
                        ),
                        apns=messaging.APNSConfig(
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    alert=messaging.ApsAlert(
                                        title=notification.title,
                                        body=notification.content
                                    ),
                                    badge=FCMService._get_user_unread_count(notification.recipient),
                                    sound='default'
                                )
                            )
                        )
                    )
                    
                    response = messaging.send(message)
                    logger.info(f"Notification push envoyée: {response}")
                    success_count += 1
                    
                except messaging.UnregisteredError:
                    # Token invalide, le marquer pour suppression
                    invalid_tokens.append(token)
                    logger.warning(f"Token FCM invalide: {token}")
                    
                except FirebaseError as e:
                    logger.error(f"Erreur Firebase pour token {token}: {e}")
                    
                except Exception as e:
                    logger.error(f"Erreur envoi push pour token {token}: {e}")
            
            # Supprimer les tokens invalides
            if invalid_tokens:
                DeviceToken.objects.filter(token__in=invalid_tokens).delete()
                logger.info(f"Tokens FCM invalides supprimés: {len(invalid_tokens)}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Erreur générale envoi push notification {notification.id}: {e}")
            return False
    
    @staticmethod
    def send_bulk_push_notification(
        user_ids: List[str], 
        title: str, 
        body: str, 
        data: Optional[Dict] = None
    ) -> Dict[str, int]:
        """
        Envoie une notification push en masse.
        
        Args:
            user_ids: Liste des IDs utilisateurs
            title: Titre de la notification
            body: Corps de la notification
            data: Données additionnelles
            
        Returns:
            Dict avec les statistiques d'envoi
        """
        try:
            # Récupérer tous les tokens actifs pour ces utilisateurs
            device_tokens = DeviceToken.objects.filter(
                user_id__in=user_ids,
                is_active=True
            ).values_list('token', flat=True)
            
            if not device_tokens:
                logger.warning("Aucun token FCM pour les utilisateurs spécifiés")
                return {'success': 0, 'failed': 0}
            
            # Préparer le message
            message_data = data or {}
            message_data.update({
                'notification_type': 'bulk',
                'timestamp': str(int(timezone.now().timestamp()))
            })
            
            # Envoyer en batch (max 500 par batch selon Firebase)
            batch_size = 500
            total_success = 0
            total_failed = 0
            invalid_tokens = []
            
            for i in range(0, len(device_tokens), batch_size):
                batch_tokens = list(device_tokens)[i:i + batch_size]
                
                try:
                    message = messaging.MulticastMessage(
                        notification=messaging.Notification(
                            title=title,
                            body=body
                        ),
                        data=message_data,
                        tokens=batch_tokens,
                        android=messaging.AndroidConfig(
                            priority='high',
                            notification=messaging.AndroidNotification(
                                icon='ic_notification',
                                color='#1976D2',
                                sound='default'
                            )
                        ),
                        apns=messaging.APNSConfig(
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    alert=messaging.ApsAlert(title=title, body=body),
                                    sound='default'
                                )
                            )
                        )
                    )
                    
                    response = messaging.send_multicast(message)
                    total_success += response.success_count
                    total_failed += response.failure_count
                    
                    # Traiter les échecs pour identifier les tokens invalides
                    if response.failure_count > 0:
                        for idx, result in enumerate(response.responses):
                            if not result.success:
                                token = batch_tokens[idx]
                                if isinstance(result.exception, messaging.UnregisteredError):
                                    invalid_tokens.append(token)
                    
                    logger.info(f"Batch envoyé: {response.success_count} succès, {response.failure_count} échecs")
                    
                except Exception as e:
                    logger.error(f"Erreur envoi batch: {e}")
                    total_failed += len(batch_tokens)
            
            # Supprimer les tokens invalides
            if invalid_tokens:
                DeviceToken.objects.filter(token__in=invalid_tokens).delete()
                logger.info(f"Tokens FCM invalides supprimés: {len(invalid_tokens)}")
            
            return {
                'success': total_success,
                'failed': total_failed,
                'invalid_tokens_removed': len(invalid_tokens)
            }
            
        except Exception as e:
            logger.error(f"Erreur envoi bulk push notification: {e}")
            return {'success': 0, 'failed': len(user_ids)}
    
    @staticmethod
    def _prepare_message_data(notification: Notification) -> Dict[str, str]:
        """
        Prépare les données du message FCM.
        
        Args:
            notification: Instance de notification
            
        Returns:
            Dict avec les données du message
        """
        data = {
            'notification_id': str(notification.id),
            'category': notification.category,
            'priority': notification.priority,
            'timestamp': str(int(notification.created_at.timestamp()))
        }
        
        # Ajouter l'URL d'action si disponible
        if notification.action_url:
            data['action_url'] = notification.action_url
        
        # Ajouter les données de l'objet lié si disponible
        if notification.related_object:
            data['related_object_type'] = notification.content_type.model
            data['related_object_id'] = str(notification.object_id)
        
        return data
    
    @staticmethod
    def _get_user_unread_count(user) -> int:
        """
        Récupère le nombre de notifications non lues pour un utilisateur.
        
        Args:
            user: Instance utilisateur
            
        Returns:
            int: Nombre de notifications non lues
        """
        try:
            from apps.notifications.models import NotificationStatus
            return user.notifications.filter(
                status=NotificationStatus.UNREAD
            ).count()
        except Exception:
            return 0
    
    @staticmethod
    def subscribe_to_topic(tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Abonne des tokens à un topic FCM.
        
        Args:
            tokens: Liste des tokens FCM
            topic: Nom du topic
            
        Returns:
            Dict avec les statistiques d'abonnement
        """
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            
            logger.info(f"Abonnement topic '{topic}': {response.success_count} succès, {response.failure_count} échecs")
            
            return {
                'success': response.success_count,
                'failed': response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Erreur abonnement topic '{topic}': {e}")
            return {'success': 0, 'failed': len(tokens)}
    
    @staticmethod
    def unsubscribe_from_topic(tokens: List[str], topic: str) -> Dict[str, int]:
        """
        Désabonne des tokens d'un topic FCM.
        
        Args:
            tokens: Liste des tokens FCM
            topic: Nom du topic
            
        Returns:
            Dict avec les statistiques de désabonnement
        """
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            logger.info(f"Désabonnement topic '{topic}': {response.success_count} succès, {response.failure_count} échecs")
            
            return {
                'success': response.success_count,
                'failed': response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Erreur désabonnement topic '{topic}': {e}")
            return {'success': 0, 'failed': len(tokens)}
    
    @staticmethod
    def send_topic_notification(
        topic: str, 
        title: str, 
        body: str, 
        data: Optional[Dict] = None
    ) -> bool:
        """
        Envoie une notification à un topic.
        
        Args:
            topic: Nom du topic
            title: Titre de la notification
            body: Corps de la notification
            data: Données additionnelles
            
        Returns:
            bool: True si envoyé avec succès
        """
        try:
            message_data = data or {}
            message_data.update({
                'notification_type': 'topic',
                'topic': topic,
                'timestamp': str(int(timezone.now().timestamp()))
            })
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=message_data,
                topic=topic,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#1976D2',
                        sound='default'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(title=title, body=body),
                            sound='default'
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"Notification topic '{topic}' envoyée: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi notification topic '{topic}': {e}")
            return False 