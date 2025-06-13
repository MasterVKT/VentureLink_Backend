"""
Service pour la gestion des paiements.
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Union, List, Tuple

from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.payments.models import Payment, Refund
from apps.core.services.payment_service import MyCoolPayService
from apps.core.services.currency_service import CurrencyService


logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service pour la gestion des paiements avec My-CoolPay.
    
    Ce service encapsule toutes les opérations liées aux paiements
    et fait le lien entre les modèles de l'application et l'API My-CoolPay.
    """
    
    @staticmethod
    def create_payment(
            user,
            amount: Union[Decimal, float],
            currency: str,
            description: str,
            payment_type: str = Payment.PaymentType.OTHER,
            related_object=None,
            metadata: Optional[Dict[str, Any]] = None,
            success_url: Optional[str] = None,
            cancel_url: Optional[str] = None,
            statement_descriptor: Optional[str] = None,
            is_test: bool = False
        ) -> Payment:
        """
        Crée un nouveau paiement.
        
        Args:
            user: Utilisateur qui effectue le paiement
            amount: Montant à payer
            currency: Code de la devise (EUR, USD, etc.)
            description: Description du paiement
            payment_type: Type de paiement (voir Payment.PaymentType)
            related_object: Objet lié au paiement (optionnel)
            metadata: Données supplémentaires à stocker
            success_url: URL de redirection après paiement réussi
            cancel_url: URL de redirection en cas d'annulation
            statement_descriptor: Description qui apparaîtra sur le relevé bancaire
            is_test: Indique s'il s'agit d'un paiement de test
            
        Returns:
            Payment: Objet Payment créé
        """
        # Créer l'enregistrement de paiement en BDD
        with transaction.atomic():
            payment = Payment(
                user=user,
                amount=Decimal(amount),
                currency=currency.upper(),
                description=description,
                payment_type=payment_type,
                metadata=metadata or {},
                is_test=is_test
            )
            
            # Ajouter l'objet lié si fourni
            if related_object:
                payment.content_type = ContentType.objects.get_for_model(related_object)
                payment.object_id = related_object.pk
            
            payment.save()
            
            # Créer le paiement via l'API My-CoolPay
            try:
                mycoolpay_service = MyCoolPayService()
                payment_response = mycoolpay_service.create_payment(
                    amount=amount,
                    currency=currency,
                    description=description,
                    customer_email=user.email,
                    metadata={
                        'payment_id': str(payment.id),
                        'payment_type': payment_type,
                        'user_id': str(user.id),
                        **(metadata or {})
                    },
                    success_url=success_url,
                    cancel_url=cancel_url,
                    statement_descriptor=statement_descriptor
                )
                
                # Mettre à jour le paiement avec les informations de My-CoolPay
                payment.external_payment_id = payment_response['payment_id']
                payment.external_checkout_url = payment_response['payment_url']
                payment.status = PaymentService._map_mycoolpay_status(payment_response['status'])
                payment.save()
                
                return payment
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du paiement My-CoolPay: {str(e)}")
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                raise
    
    @staticmethod
    def update_payment_status(payment_id: str) -> Payment:
        """
        Met à jour le statut d'un paiement depuis My-CoolPay.
        
        Args:
            payment_id: ID du paiement à mettre à jour
            
        Returns:
            Payment: Objet Payment mis à jour
            
        Raises:
            Payment.DoesNotExist: Si le paiement n'existe pas
        """
        payment = Payment.objects.get(id=payment_id)
        
        if not payment.external_payment_id:
            logger.warning(f"Impossible de mettre à jour le statut du paiement {payment_id}: pas d'ID externe")
            return payment
        
        try:
            mycoolpay_service = MyCoolPayService()
            payment_status = mycoolpay_service.get_payment_status(payment.external_payment_id)
            
            # Mettre à jour le paiement avec les informations de My-CoolPay
            new_status = PaymentService._map_mycoolpay_status(payment_status['status'])
            
            if new_status != payment.status:
                old_status = payment.status
                payment.status = new_status
                
                # Si le paiement vient d'être complété
                if new_status == Payment.PaymentStatus.COMPLETED and old_status != Payment.PaymentStatus.COMPLETED:
                    payment.completed_at = timezone.now()
                
                payment.save()
                
                # Journaliser le changement de statut
                logger.info(f"Statut du paiement {payment_id} mis à jour: {old_status} -> {new_status}")
            
            return payment
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut du paiement {payment_id}: {str(e)}")
            raise
    
    @staticmethod
    def refund_payment(
            payment_id: str,
            amount: Optional[Union[Decimal, float]] = None,
            reason: Optional[str] = None,
            notes: Optional[str] = None
        ) -> Tuple[Payment, Refund]:
        """
        Rembourse un paiement.
        
        Args:
            payment_id: ID du paiement à rembourser
            amount: Montant à rembourser (si non spécifié, rembourse la totalité)
            reason: Raison du remboursement
            notes: Notes internes sur le remboursement
            
        Returns:
            Tuple[Payment, Refund]: Objets Payment et Refund mis à jour
            
        Raises:
            Payment.DoesNotExist: Si le paiement n'existe pas
            ValueError: Si le paiement ne peut pas être remboursé
        """
        payment = Payment.objects.get(id=payment_id)
        
        # Vérifier que le paiement peut être remboursé
        if not payment.can_be_refunded:
            raise ValueError(f"Le paiement {payment_id} ne peut pas être remboursé (statut: {payment.status})")
        
        if not payment.external_payment_id:
            raise ValueError(f"Le paiement {payment_id} n'a pas d'ID externe et ne peut pas être remboursé")
        
        # Si le montant n'est pas spécifié, rembourser la totalité
        refund_amount = Decimal(amount) if amount is not None else payment.amount
        
        # Vérifier que le montant est valide
        if refund_amount <= 0 or refund_amount > payment.amount:
            raise ValueError(f"Montant de remboursement invalide: {refund_amount}")
        
        with transaction.atomic():
            # Créer l'enregistrement de remboursement en BDD
            refund = Refund(
                payment=payment,
                amount=refund_amount,
                currency=payment.currency,
                reason=reason or '',
                notes=notes or ''
            )
            refund.save()
            
            # Effectuer le remboursement via My-CoolPay
            try:
                mycoolpay_service = MyCoolPayService()
                refund_response = mycoolpay_service.refund_payment(
                    payment_id=payment.external_payment_id,
                    amount=float(refund_amount) if amount is not None else None,
                    reason=reason
                )
                
                # Mettre à jour le remboursement avec les informations de My-CoolPay
                refund.external_refund_id = refund_response['refund_id']
                refund.status = PaymentService._map_mycoolpay_refund_status(refund_response['status'])
                
                if refund.status == Refund.RefundStatus.COMPLETED:
                    refund.completed_at = timezone.now()
                
                refund.save()
                
                # Mettre à jour le statut du paiement
                if refund_amount == payment.amount:
                    payment.status = Payment.PaymentStatus.REFUNDED
                else:
                    payment.status = Payment.PaymentStatus.PARTIALLY_REFUNDED
                
                payment.save()
                
                return payment, refund
                
            except Exception as e:
                logger.error(f"Erreur lors du remboursement du paiement {payment_id}: {str(e)}")
                refund.status = Refund.RefundStatus.FAILED
                refund.save()
                raise
    
    @staticmethod
    def handle_webhook_event(event_data: Dict[str, Any]) -> Optional[Payment]:
        """
        Traite un événement webhook de My-CoolPay.
        
        Args:
            event_data: Données de l'événement webhook
            
        Returns:
            Optional[Payment]: Objet Payment mis à jour, si applicable
        """
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        if not event_type or not data:
            logger.warning("Événement webhook invalide: données manquantes")
            return None
        
        # Traiter selon le type d'événement
        if event_type == 'payment.updated':
            payment_id = data.get('metadata', {}).get('payment_id')
            if not payment_id:
                logger.warning("ID de paiement manquant dans les métadonnées de l'événement webhook")
                return None
            
            try:
                payment = Payment.objects.get(id=payment_id)
                return PaymentService.update_payment_status(payment_id)
            except Payment.DoesNotExist:
                logger.warning(f"Paiement {payment_id} non trouvé lors du traitement du webhook")
                return None
                
        elif event_type == 'payment.refunded':
            # Les remboursements sont déjà traités lors de l'appel à refund_payment
            # Mais on peut quand même vérifier que tout est cohérent
            payment_id = data.get('metadata', {}).get('payment_id')
            if not payment_id:
                return None
            
            try:
                return PaymentService.update_payment_status(payment_id)
            except Payment.DoesNotExist:
                return None
        
        return None
    
    @staticmethod
    def convert_amount(amount: Union[Decimal, float], from_currency: str, 
                      to_currency: str) -> Decimal:
        """
        Convertit un montant d'une devise à une autre.
        
        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            
        Returns:
            Decimal: Montant converti
        """
        if from_currency == to_currency:
            return Decimal(amount)
        
        # Utilise le service de conversion de devises
        return CurrencyService.convert_amount(amount, from_currency, to_currency)
    
    @staticmethod
    def _map_mycoolpay_status(mycoolpay_status: str) -> str:
        """
        Convertit un statut My-CoolPay en statut Payment.
        
        Args:
            mycoolpay_status: Statut provenant de My-CoolPay
            
        Returns:
            str: Statut correspondant dans Payment.PaymentStatus
        """
        status_mapping = {
            'pending': Payment.PaymentStatus.PENDING,
            'processing': Payment.PaymentStatus.PROCESSING,
            'succeeded': Payment.PaymentStatus.COMPLETED,
            'completed': Payment.PaymentStatus.COMPLETED,
            'failed': Payment.PaymentStatus.FAILED,
            'canceled': Payment.PaymentStatus.CANCELLED,
            'refunded': Payment.PaymentStatus.REFUNDED,
            'partially_refunded': Payment.PaymentStatus.PARTIALLY_REFUNDED
        }
        
        return status_mapping.get(mycoolpay_status.lower(), Payment.PaymentStatus.PENDING)
    
    @staticmethod
    def _map_mycoolpay_refund_status(mycoolpay_status: str) -> str:
        """
        Convertit un statut de remboursement My-CoolPay en statut Refund.
        
        Args:
            mycoolpay_status: Statut provenant de My-CoolPay
            
        Returns:
            str: Statut correspondant dans Refund.RefundStatus
        """
        status_mapping = {
            'pending': Refund.RefundStatus.PENDING,
            'processing': Refund.RefundStatus.PROCESSING,
            'succeeded': Refund.RefundStatus.COMPLETED,
            'completed': Refund.RefundStatus.COMPLETED,
            'failed': Refund.RefundStatus.FAILED
        }
        
        return status_mapping.get(mycoolpay_status.lower(), Refund.RefundStatus.PENDING) 