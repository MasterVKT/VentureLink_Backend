"""
Service pour le traitement des webhooks My-CoolPay.

Ce service est responsable de la validation et du traitement des événements
de webhook envoyés par My-CoolPay lors des changements de statut des paiements.
"""
import logging
import json
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.payments.models import Payment, Refund
from apps.payments.services.mycoolpay_service import MyCoolPayService
from apps.notifications.services.notification_service import NotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service pour traiter les webhooks provenant de My-CoolPay.
    """
    
    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Vérifie la signature HMAC d'un webhook My-CoolPay.
        
        Args:
            payload: Le contenu du webhook au format JSON
            signature: La signature HMAC fournie dans l'en-tête
            secret: Le secret utilisé pour générer la signature
            
        Returns:
            bool: True si la signature est valide, False sinon
        """
        if not payload or not signature or not secret:
            return False
            
        # Calculer le HMAC avec SHA-256
        expected_signature = hmac.new(
            key=secret.encode(),
            msg=payload.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Comparer avec la signature reçue
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def process_webhook_event(event_data: dict) -> bool:
        """
        Traite un événement webhook de My-CoolPay.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        event_type = event_data.get('event_type')
        if not event_type:
            logger.error("Événement webhook sans type")
            return False
            
        logger.info(f"Traitement de l'événement webhook My-CoolPay: {event_type}")
        
        # Rediriger vers la méthode appropriée en fonction du type d'événement
        if event_type == 'payment.success':
            return WebhookService._handle_payment_success(event_data)
        elif event_type == 'payment.failed':
            return WebhookService._handle_payment_failed(event_data)
        elif event_type == 'payment.refunded':
            return WebhookService._handle_payment_refunded(event_data)
        elif event_type == 'subscription.created':
            return WebhookService._handle_subscription_created(event_data)
        elif event_type == 'subscription.cancelled':
            return WebhookService._handle_subscription_cancelled(event_data)
        elif event_type == 'subscription.renewed':
            return WebhookService._handle_subscription_renewed(event_data)
        else:
            logger.warning(f"Type d'événement webhook non géré: {event_type}")
            return False
    
    @staticmethod
    def _handle_payment_success(event_data: dict) -> bool:
        """
        Traite un événement de paiement réussi.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        transaction_ref = event_data.get('transaction_ref')
        app_transaction_ref = event_data.get('app_transaction_ref')
        
        if not transaction_ref:
            logger.error("Événement payment.success sans référence de transaction")
            return False
            
        # Rechercher le paiement correspondant
        try:
            # D'abord par référence externe
            payment = Payment.objects.filter(external_payment_id=transaction_ref).first()
            
            # Si non trouvé, essayer par notre référence interne qui peut être stockée dans app_transaction_ref
            if not payment and app_transaction_ref:
                payment = Payment.objects.filter(id=app_transaction_ref).first()
                
            if not payment:
                logger.error(f"Paiement non trouvé pour l'événement payment.success: {transaction_ref}")
                return False
                
            # Mettre à jour le statut du paiement
            with transaction.atomic():
                old_status = payment.status
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.completed_at = timezone.now()
                
                # Mettre à jour les métadonnées avec les informations supplémentaires
                if 'transaction_details' in event_data:
                    payment.metadata.update({
                        'transaction_details': event_data.get('transaction_details'),
                        'payment_method': event_data.get('payment_method'),
                        'transaction_date': event_data.get('transaction_date'),
                    })
                
                payment.save()
                
                # Traiter les actions post-paiement en fonction du type
                if payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
                    from apps.payments.services.subscription_service import SubscriptionService
                    SubscriptionService.activate_subscription_from_payment(payment)
                
                # Envoyer une notification à l'utilisateur
                if payment.user:
                    NotificationService.send_payment_success_notification(payment)
                
                logger.info(f"Paiement {payment.id} mis à jour: {old_status} -> {payment.status}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement payment.success: {str(e)}")
            return False
    
    @staticmethod
    def _handle_payment_failed(event_data: dict) -> bool:
        """
        Traite un événement de paiement échoué.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        transaction_ref = event_data.get('transaction_ref')
        app_transaction_ref = event_data.get('app_transaction_ref')
        
        if not transaction_ref:
            logger.error("Événement payment.failed sans référence de transaction")
            return False
            
        # Rechercher le paiement correspondant
        try:
            # D'abord par référence externe
            payment = Payment.objects.filter(external_payment_id=transaction_ref).first()
            
            # Si non trouvé, essayer par notre référence interne
            if not payment and app_transaction_ref:
                payment = Payment.objects.filter(id=app_transaction_ref).first()
                
            if not payment:
                logger.error(f"Paiement non trouvé pour l'événement payment.failed: {transaction_ref}")
                return False
                
            # Mettre à jour le statut du paiement
            with transaction.atomic():
                old_status = payment.status
                payment.status = Payment.PaymentStatus.FAILED
                
                # Mettre à jour les métadonnées avec les informations d'erreur
                if 'error_details' in event_data:
                    payment.metadata.update({
                        'error_details': event_data.get('error_details'),
                        'error_code': event_data.get('error_code'),
                        'failure_date': event_data.get('transaction_date'),
                    })
                
                payment.save()
                
                # Envoyer une notification à l'utilisateur
                if payment.user:
                    NotificationService.send_payment_failed_notification(payment)
                
                logger.info(f"Paiement {payment.id} mis à jour: {old_status} -> {payment.status}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement payment.failed: {str(e)}")
            return False
    
    @staticmethod
    def _handle_payment_refunded(event_data: dict) -> bool:
        """
        Traite un événement de paiement remboursé.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        transaction_ref = event_data.get('transaction_ref')
        refund_ref = event_data.get('refund_ref')
        refund_amount = event_data.get('refund_amount')
        
        if not transaction_ref or not refund_ref:
            logger.error("Événement payment.refunded avec des informations manquantes")
            return False
            
        # Rechercher le paiement correspondant
        try:
            payment = Payment.objects.filter(external_payment_id=transaction_ref).first()
            if not payment:
                logger.error(f"Paiement non trouvé pour l'événement payment.refunded: {transaction_ref}")
                return False
                
            # Vérifier si le remboursement existe déjà
            existing_refund = Refund.objects.filter(external_refund_id=refund_ref).first()
            if existing_refund:
                # Mettre à jour le statut du remboursement existant
                existing_refund.status = Refund.RefundStatus.COMPLETED
                existing_refund.completed_at = timezone.now()
                existing_refund.save()
                
                logger.info(f"Remboursement {existing_refund.id} marqué comme complété")
                return True
                
            # Créer un nouveau remboursement
            with transaction.atomic():
                # Déterminer le montant du remboursement
                amount = float(refund_amount) if refund_amount else float(payment.amount)
                
                # Créer l'enregistrement de remboursement
                refund = Refund(
                    payment=payment,
                    amount=amount,
                    currency=payment.currency,
                    status=Refund.RefundStatus.COMPLETED,
                    external_refund_id=refund_ref,
                    reason=event_data.get('refund_reason', ''),
                    completed_at=timezone.now()
                )
                refund.save()
                
                # Mettre à jour le statut du paiement
                old_status = payment.status
                
                # Si le remboursement est total
                if amount >= payment.amount:
                    payment.status = Payment.PaymentStatus.REFUNDED
                else:
                    payment.status = Payment.PaymentStatus.PARTIALLY_REFUNDED
                
                payment.save()
                
                # Envoyer une notification à l'utilisateur
                if payment.user:
                    NotificationService.send_refund_notification(payment, refund)
                
                logger.info(f"Paiement {payment.id} remboursé: {old_status} -> {payment.status}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement payment.refunded: {str(e)}")
            return False
    
    @staticmethod
    def _handle_subscription_created(event_data: dict) -> bool:
        """
        Traite un événement de création d'abonnement.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        # Déléguer au service d'abonnement
        from apps.payments.services.subscription_service import SubscriptionService
        return SubscriptionService.handle_subscription_created_webhook(event_data)
    
    @staticmethod
    def _handle_subscription_cancelled(event_data: dict) -> bool:
        """
        Traite un événement d'annulation d'abonnement.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        # Déléguer au service d'abonnement
        from apps.payments.services.subscription_service import SubscriptionService
        return SubscriptionService.handle_subscription_cancelled_webhook(event_data)
    
    @staticmethod
    def _handle_subscription_renewed(event_data: dict) -> bool:
        """
        Traite un événement de renouvellement d'abonnement.
        
        Args:
            event_data: Les données de l'événement
            
        Returns:
            bool: True si l'événement a été traité avec succès
        """
        # Déléguer au service d'abonnement
        from apps.payments.services.subscription_service import SubscriptionService
        return SubscriptionService.handle_subscription_renewed_webhook(event_data) 