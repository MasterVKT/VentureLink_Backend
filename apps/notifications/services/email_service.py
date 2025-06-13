"""
Service d'envoi d'emails pour les notifications.
"""
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service pour envoyer des notifications par email.
    """
    
    @staticmethod
    def send_email_notification(notification: Notification) -> bool:
        """
        Envoie une notification par email.
        
        Args:
            notification: Instance de notification à envoyer
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        try:
            recipient_email = notification.recipient.email
            
            if not recipient_email:
                logger.warning(f"Pas d'email pour l'utilisateur {notification.recipient.id}")
                return False
            
            # Préparer le contexte pour le template
            context = {
                'notification': notification,
                'user': notification.recipient,
                'user_name': notification.recipient.get_full_name() or notification.recipient.email,
                'site_name': 'VentureLink',
                'site_url': settings.FRONTEND_URL,
                'unsubscribe_url': f"{settings.FRONTEND_URL}/notifications/unsubscribe/{notification.recipient.id}",
            }
            
            # Déterminer le template selon la catégorie
            template_name = EmailNotificationService._get_template_name(notification.category)
            
            # Générer le contenu HTML et texte
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Créer l'email
            subject = f"[VentureLink] {notification.title}"
            from_email = settings.DEFAULT_FROM_EMAIL
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer l'email
            email.send()
            
            logger.info(f"Email notification envoyé à {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email notification {notification.id}: {e}")
            return False
    
    @staticmethod
    def send_bulk_email_notification(
        recipients: List[str], 
        subject: str, 
        template_name: str, 
        context: Dict
    ) -> Dict[str, int]:
        """
        Envoie des emails en masse.
        
        Args:
            recipients: Liste des emails destinataires
            subject: Sujet de l'email
            template_name: Nom du template à utiliser
            context: Contexte pour le template
            
        Returns:
            Dict avec les statistiques d'envoi
        """
        try:
            success_count = 0
            failed_count = 0
            
            # Préparer le contexte de base
            base_context = {
                'site_name': 'VentureLink',
                'site_url': settings.FRONTEND_URL,
                **context
            }
            
            # Générer le contenu HTML et texte
            html_content = render_to_string(f'emails/{template_name}.html', base_context)
            text_content = strip_tags(html_content)
            
            from_email = settings.DEFAULT_FROM_EMAIL
            
            for recipient_email in recipients:
                try:
                    # Personnaliser le contexte pour chaque destinataire
                    personal_context = {
                        **base_context,
                        'unsubscribe_url': f"{settings.FRONTEND_URL}/notifications/unsubscribe/{recipient_email}",
                    }
                    
                    # Re-générer le contenu avec le contexte personnalisé
                    personal_html = render_to_string(f'emails/{template_name}.html', personal_context)
                    personal_text = strip_tags(personal_html)
                    
                    email = EmailMultiAlternatives(
                        subject=f"[VentureLink] {subject}",
                        body=personal_text,
                        from_email=from_email,
                        to=[recipient_email]
                    )
                    
                    email.attach_alternative(personal_html, "text/html")
                    email.send()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erreur envoi email à {recipient_email}: {e}")
                    failed_count += 1
            
            logger.info(f"Emails en masse envoyés: {success_count} succès, {failed_count} échecs")
            
            return {
                'success': success_count,
                'failed': failed_count
            }
            
        except Exception as e:
            logger.error(f"Erreur envoi emails en masse: {e}")
            return {'success': 0, 'failed': len(recipients)}
    
    @staticmethod
    def send_welcome_email(user) -> bool:
        """
        Envoie un email de bienvenue à un nouvel utilisateur.
        
        Args:
            user: Instance utilisateur
            
        Returns:
            bool: True si envoyé avec succès
        """
        try:
            context = {
                'user': user,
                'user_name': user.get_full_name() or user.email,
                'site_name': 'VentureLink',
                'site_url': settings.FRONTEND_URL,
                'login_url': f"{settings.FRONTEND_URL}/login",
                'profile_url': f"{settings.FRONTEND_URL}/profile",
            }
            
            html_content = render_to_string('emails/welcome.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject="[VentureLink] Bienvenue sur VentureLink !",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Email de bienvenue envoyé à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email de bienvenue à {user.email}: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, reset_token: str) -> bool:
        """
        Envoie un email de réinitialisation de mot de passe.
        
        Args:
            user: Instance utilisateur
            reset_token: Token de réinitialisation
            
        Returns:
            bool: True si envoyé avec succès
        """
        try:
            context = {
                'user': user,
                'user_name': user.get_full_name() or user.email,
                'site_name': 'VentureLink',
                'reset_url': f"{settings.FRONTEND_URL}/reset-password/{reset_token}",
                'site_url': settings.FRONTEND_URL,
            }
            
            html_content = render_to_string('emails/password_reset.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject="[VentureLink] Réinitialisation de votre mot de passe",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Email de réinitialisation envoyé à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email de réinitialisation à {user.email}: {e}")
            return False
    
    @staticmethod
    def send_email_verification(user, verification_token: str) -> bool:
        """
        Envoie un email de vérification d'adresse email.
        
        Args:
            user: Instance utilisateur
            verification_token: Token de vérification
            
        Returns:
            bool: True si envoyé avec succès
        """
        try:
            context = {
                'user': user,
                'user_name': user.get_full_name() or user.email,
                'site_name': 'VentureLink',
                'verification_url': f"{settings.FRONTEND_URL}/verify-email/{verification_token}",
                'site_url': settings.FRONTEND_URL,
            }
            
            html_content = render_to_string('emails/email_verification.html', context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject="[VentureLink] Vérifiez votre adresse email",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Email de vérification envoyé à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email de vérification à {user.email}: {e}")
            return False
    
    @staticmethod
    def _get_template_name(category: str) -> str:
        """
        Détermine le nom du template selon la catégorie de notification.
        
        Args:
            category: Catégorie de la notification
            
        Returns:
            str: Nom du template
        """
        template_mapping = {
            'PROJECT': 'project_notification',
            'INVESTMENT': 'investment_notification',
            'MESSAGE': 'message_notification',
            'PAYMENT': 'payment_notification',
            'SYSTEM': 'system_notification',
            'GENERAL': 'general_notification',
        }
        
        return template_mapping.get(category, 'general_notification') 