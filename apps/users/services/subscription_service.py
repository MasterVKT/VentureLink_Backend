"""
Service pour la gestion des abonnements utilisateurs.
"""
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from apps.users.models import User, Subscription, SubscriptionTransaction
from apps.users.services.payment_service import PaymentService
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PaymentError

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Service pour la gestion des abonnements utilisateurs.
    """
    
    @staticmethod
    def get_user_subscription(user_id):
        """
        Récupère l'abonnement d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Subscription: L'abonnement de l'utilisateur
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
        """
        try:
            user = User.objects.get(id=user_id)
            return Subscription.objects.filter(user=user).order_by('-created_at').first()
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
    
    @staticmethod
    @transaction.atomic
    def create_subscription(user_id, plan, payment_method=None, payment_id=None):
        """
        Crée un nouvel abonnement pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            plan (str): Le plan d'abonnement choisi
            payment_method (str, optional): Méthode de paiement
            payment_id (str, optional): ID de la transaction de paiement
            
        Returns:
            Subscription: Le nouvel abonnement créé
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
            ValidationError: Si les données d'abonnement sont invalides
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Vérifier si l'utilisateur a déjà un abonnement actif
            active_subscription = Subscription.objects.filter(
                user=user,
                status='ACTIVE',
                end_date__gt=timezone.now()
            ).first()
            
            if active_subscription:
                raise ValidationError("L'utilisateur a déjà un abonnement actif")
            
            # Déterminer la date d'expiration en fonction du plan
            if plan == 'PREMIUM_MONTHLY':
                expiry_date = timezone.now() + timedelta(days=30)
            elif plan == 'PREMIUM_YEARLY':
                expiry_date = timezone.now() + timedelta(days=365)
            elif plan == 'FREE':
                expiry_date = None
            else:
                raise ValidationError("Plan d'abonnement non valide")
            
            # Créer le nouvel abonnement
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                status='ACTIVE',
                start_date=timezone.now(),
                end_date=expiry_date,
                auto_renew=True if plan != 'FREE' else False,
                payment_provider='MY_COOLPAY' if payment_id else None,
                payment_id=payment_id
            )
            
            # Mettre à jour le statut premium de l'utilisateur
            user.is_premium = plan != 'FREE'
            user.save(update_fields=['is_premium'])
            
            # Créer la transaction si un ID de paiement est fourni
            if payment_id and plan != 'FREE':
                # Déterminer le montant en fonction du plan
                amount = 9.99 if plan == 'PREMIUM_MONTHLY' else 99.99
                
                SubscriptionTransaction.objects.create(
                    subscription=subscription,
                    amount=amount,
                    currency='EUR',  # Par défaut
                    transaction_id=payment_id,
                    payment_method=payment_method or 'CARD',
                    status='COMPLETED'
                )
            
            return subscription
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
    
    @staticmethod
    @transaction.atomic
    def cancel_subscription(subscription_id, user_id, cancel_reason=None):
        """
        Annule un abonnement.
        
        Args:
            subscription_id: ID de l'abonnement
            user_id: ID de l'utilisateur
            cancel_reason (str, optional): Raison de l'annulation
            
        Returns:
            Subscription: L'abonnement annulé
            
        Raises:
            ResourceNotFoundError: Si l'abonnement ou l'utilisateur n'existe pas
            ValidationError: Si l'utilisateur n'est pas le propriétaire de l'abonnement
        """
        try:
            user = User.objects.get(id=user_id)
            subscription = Subscription.objects.get(id=subscription_id)
            
            # Vérifier que l'abonnement appartient à l'utilisateur
            if subscription.user != user:
                raise ValidationError("Cet abonnement n'appartient pas à l'utilisateur")
            
            # Annuler l'abonnement
            subscription.status = 'CANCELLED'
            subscription.auto_renew = False
            subscription.save(update_fields=['status', 'auto_renew'])
            
            # Si l'abonnement a un ID de paiement et est encore actif, on peut tenter d'annuler avec le provider
            if subscription.payment_id and subscription.payment_provider == 'MY_COOLPAY' and subscription.end_date > timezone.now():
                try:
                    payment_service = PaymentService()
                    payment_service.cancel_payment(subscription.payment_id)
                except PaymentError as e:
                    logger.error(f"Erreur lors de l'annulation du paiement: {str(e)}")
                    # L'erreur n'empêche pas l'annulation côté application
            
            return subscription
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
        except Subscription.DoesNotExist:
            raise ResourceNotFoundError("Abonnement non trouvé")
            
    @staticmethod
    def init_subscription_payment(user_id, plan, currency="EUR", return_url=None):
        """
        Initialise un paiement pour un abonnement premium.
        
        Args:
            user_id: ID de l'utilisateur
            plan (str): Le plan d'abonnement (PREMIUM_MONTHLY, PREMIUM_YEARLY)
            currency (str, optional): La devise du paiement
            return_url (str, optional): URL de retour après paiement
            
        Returns:
            dict: Les informations de paiement (checkout_url, checkout_id)
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
            ValidationError: Si le plan n'est pas valide
            PaymentError: Si une erreur se produit lors de l'initialisation du paiement
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Vérifier que le plan est valide
            if plan not in ['PREMIUM_MONTHLY', 'PREMIUM_YEARLY']:
                raise ValidationError("Plan d'abonnement non valide pour le paiement")
            
            # Vérifier si l'utilisateur a déjà un abonnement actif
            active_subscription = Subscription.objects.filter(
                user=user,
                status='ACTIVE',
                end_date__gt=timezone.now()
            ).first()
            
            if active_subscription and active_subscription.plan != 'FREE':
                raise ValidationError("L'utilisateur a déjà un abonnement premium actif")
            
            # Initialiser le paiement via My-CoolPay
            payment_service = PaymentService()
            payment_info = payment_service.init_subscription_payment(
                user=user,
                plan=plan,
                currency=currency,
                return_url=return_url
            )
            
            return payment_info
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
        
    @staticmethod
    def process_payment_webhook(event_type, event_data):
        """
        Traite les notifications webhook de paiement.
        
        Args:
            event_type (str): Type d'événement (payment.succeeded, payment.failed, etc.)
            event_data (dict): Données de l'événement
            
        Returns:
            bool: True si le traitement a réussi, False sinon
        """
        logger.info(f"Traitement du webhook de paiement: {event_type}")
        
        try:
            # Extraire les informations du webhook
            payment_id = event_data.get('payment_id')
            if not payment_id:
                logger.error("Webhook sans ID de paiement")
                return False
            
            metadata = event_data.get('metadata', {})
            user_id = metadata.get('user_id')
            plan = metadata.get('plan')
            
            if not user_id or not plan:
                logger.error("Métadonnées incomplètes dans le webhook")
                return False
            
            # Traiter selon le type d'événement
            if event_type == 'payment.succeeded':
                # Créer ou mettre à jour l'abonnement
                payment_method = event_data.get('payment_method', {}).get('type', 'CARD')
                subscription = SubscriptionService.create_subscription(
                    user_id=user_id,
                    plan=plan,
                    payment_method=payment_method,
                    payment_id=payment_id
                )
                logger.info(f"Abonnement {subscription.id} créé suite au paiement réussi")
                return True
                
            elif event_type == 'payment.failed':
                # Enregistrer l'échec de paiement
                logger.warning(f"Échec de paiement pour l'utilisateur {user_id}, plan {plan}")
                
                # Trouver l'abonnement en attente s'il existe
                user = User.objects.get(id=user_id)
                pending_subscription = Subscription.objects.filter(
                    user=user,
                    payment_id=payment_id
                ).first()
                
                if pending_subscription:
                    pending_subscription.status = 'FAILED'
                    pending_subscription.save(update_fields=['status'])
                
                return True
                
            elif event_type == 'subscription.cancelled':
                # Traiter l'annulation d'abonnement
                subscription = Subscription.objects.filter(
                    payment_id=payment_id
                ).first()
                
                if subscription:
                    subscription.status = 'CANCELLED'
                    subscription.auto_renew = False
                    subscription.save(update_fields=['status', 'auto_renew'])
                    logger.info(f"Abonnement {subscription.id} annulé via webhook")
                    
                    # Vérifier si l'utilisateur a d'autres abonnements actifs
                    has_active_subscriptions = Subscription.objects.filter(
                        user=subscription.user,
                        status='ACTIVE',
                        end_date__gt=timezone.now()
                    ).exclude(id=subscription.id).exists()
                    
                    # Si non, mettre à jour le statut premium
                    if not has_active_subscriptions:
                        subscription.user.is_premium = False
                        subscription.user.save(update_fields=['is_premium'])
                
                return True
                
            else:
                logger.info(f"Type d'événement webhook non traité: {event_type}")
                return True  # On considère que c'est traité même si on ne fait rien
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
            return False
                
    @staticmethod
    def get_subscription_transactions(subscription_id, user_id):
        """
        Récupère les transactions liées à un abonnement.
        
        Args:
            subscription_id: ID de l'abonnement
            user_id: ID de l'utilisateur pour vérification
            
        Returns:
            QuerySet: Liste des transactions
            
        Raises:
            ResourceNotFoundError: Si l'abonnement ou l'utilisateur n'existe pas
            ValidationError: Si l'utilisateur n'est pas le propriétaire de l'abonnement
        """
        try:
            user = User.objects.get(id=user_id)
            subscription = Subscription.objects.get(id=subscription_id)
            
            # Vérifier que l'abonnement appartient à l'utilisateur
            if subscription.user != user:
                raise ValidationError("Cet abonnement n'appartient pas à l'utilisateur")
            
            return SubscriptionTransaction.objects.filter(
                subscription=subscription
            ).order_by('-created_at')
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
        except Subscription.DoesNotExist:
            raise ResourceNotFoundError("Abonnement non trouvé")
            
    @staticmethod
    def update_auto_renewal(subscription_id, user_id, auto_renew):
        """
        Met à jour le paramètre de renouvellement automatique.
        
        Args:
            subscription_id: ID de l'abonnement
            user_id: ID de l'utilisateur
            auto_renew (bool): État du renouvellement automatique
            
        Returns:
            Subscription: L'abonnement modifié
            
        Raises:
            ResourceNotFoundError: Si l'abonnement ou l'utilisateur n'existe pas
            ValidationError: Si l'utilisateur n'est pas le propriétaire de l'abonnement
        """
        try:
            user = User.objects.get(id=user_id)
            subscription = Subscription.objects.get(id=subscription_id)
            
            # Vérifier que l'abonnement appartient à l'utilisateur
            if subscription.user != user:
                raise ValidationError("Cet abonnement n'appartient pas à l'utilisateur")
            
            # Mettre à jour le paramètre
            subscription.auto_renew = bool(auto_renew)
            subscription.save(update_fields=['auto_renew'])
            
            return subscription
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
        except Subscription.DoesNotExist:
            raise ResourceNotFoundError("Abonnement non trouvé") 