"""
Service d'intégration My-CoolPay pour VentureLink
CORRIGÉ: Utilisation des modèles unifiés SubscriptionPlan et UserSubscription
"""
import requests
import json
import logging
import hashlib
import hmac
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import datetime

# Import des modèles unifiés (CORRECCIÓN)
from apps.payments.models import (
    Payment, 
    PaymentMethod, 
    PaymentStatus,
    SubscriptionPlan,    # ✅ Modèle unifié
    UserSubscription,    # ✅ Modèle unifié
)

logger = logging.getLogger(__name__)


class MyCoolPayError(Exception):
    """Exception pour les erreurs My-CoolPay"""
    pass


class MyCoolPayService:
    """Service d'intégration My-CoolPay avec modèles unifiés"""
    
    # URLs d'API
    SANDBOX_BASE_URL = "https://sandbox.my-coolpay.com/api/v1"
    PRODUCTION_BASE_URL = "https://api.my-coolpay.com/api/v1"
    
    # Devises supportées
    SUPPORTED_CURRENCIES = ['XAF', 'EUR', 'USD', 'XOF']
    
    # Opérateurs de paiement mobile
    MOBILE_OPERATORS = {
        'CM_OM': 'Orange Money Cameroun',
        'CM_MOMO': 'MTN Mobile Money Cameroun',
        'SN_OM': 'Orange Money Sénégal',
        'CI_OM': 'Orange Money Côte d\'Ivoire',
        'EU_CARD': 'Carte bancaire européenne'
    }
    
    def __init__(self, sandbox: bool = True):
        """
        Initialiser le service My-CoolPay
        
        Args:
            sandbox: Utiliser l'environnement sandbox si True
        """
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL
        
        # Clés API depuis les settings Django
        if sandbox:
            self.public_key = getattr(settings, 'MYCOOLPAY_SANDBOX_PUBLIC_KEY', '')
            self.private_key = getattr(settings, 'MYCOOLPAY_SANDBOX_PRIVATE_KEY', '')
        else:
            self.public_key = getattr(settings, 'MYCOOLPAY_PUBLIC_KEY', '')
            self.private_key = getattr(settings, 'MYCOOLPAY_PRIVATE_KEY', '')
            
        if not self.public_key or not self.private_key:
            raise MyCoolPayError("Clés API My-CoolPay manquantes dans les settings")
    
    def _make_request(self, endpoint: str, method: str = 'POST', data: Dict = None) -> Dict[str, Any]:
        """
        Effectuer une requête à l'API My-CoolPay
        
        Args:
            endpoint: Point de terminaison de l'API
            method: Méthode HTTP
            data: Données à envoyer
            
        Returns:
            Réponse de l'API
            
        Raises:
            MyCoolPayError: En cas d'erreur API
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.public_key}',
            'Accept': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            else:
                response = requests.request(
                    method.upper(), 
                    url, 
                    headers=headers, 
                    json=data, 
                    timeout=30
                )
            
            logger.info(f"My-CoolPay {method} {endpoint} - Status: {response.status_code}")
            
            # Vérifier le statut de la réponse
            if response.status_code >= 400:
                error_msg = f"Erreur API My-CoolPay: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Erreur inconnue')}"
                except:
                    error_msg += f" - {response.text}"
                
                logger.error(error_msg)
                raise MyCoolPayError(error_msg)
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Erreur de connexion My-CoolPay: {str(e)}")
            raise MyCoolPayError(f"Erreur de connexion: {str(e)}")
    
    def create_paylink(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Créer un lien de paiement My-CoolPay
        
        Args:
            payment_data: Données du paiement
            
        Returns:
            Réponse contenant l'URL de paiement et la référence
        """
        # Validation des données requises
        required_fields = [
            'transaction_amount', 'transaction_currency', 'transaction_reason',
            'app_transaction_ref', 'customer_phone_number', 'customer_name',
            'customer_email'
        ]
        
        for field in required_fields:
            if field not in payment_data:
                raise MyCoolPayError(f"Champ requis manquant: {field}")
        
        # Vérifier la devise
        currency = payment_data['transaction_currency']
        if currency not in self.SUPPORTED_CURRENCIES:
            raise MyCoolPayError(f"Devise non supportée: {currency}")
        
        # Ajouter les paramètres par défaut
        data = {
            **payment_data,
            'customer_lang': payment_data.get('customer_lang', 'fr'),
            'return_url': payment_data.get('return_url', settings.SITE_URL + '/payments/success/'),
            'cancel_url': payment_data.get('cancel_url', settings.SITE_URL + '/payments/cancel/'),
            'callback_url': payment_data.get('callback_url', settings.SITE_URL + '/api/v1/payments/mycoolpay/callback/')
        }
        
        return self._make_request('paylink', 'POST', data)
    
    def initiate_payin(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initier un paiement direct (payin)
        
        Args:
            payment_data: Données du paiement avec opérateur spécifique
            
        Returns:
            Réponse avec l'action suivante (REQUIRE_OTP, PENDING, etc.)
        """
        # Validation
        required_fields = [
            'transaction_amount', 'transaction_currency', 'transaction_reason',
            'app_transaction_ref', 'customer_phone_number', 'customer_name',
            'customer_email', 'transaction_operator'
        ]
        
        for field in required_fields:
            if field not in payment_data:
                raise MyCoolPayError(f"Champ requis manquant: {field}")
        
        # Vérifier l'opérateur
        operator = payment_data['transaction_operator']
        if operator not in self.MOBILE_OPERATORS:
            raise MyCoolPayError(f"Opérateur non supporté: {operator}")
        
        return self._make_request('payin', 'POST', payment_data)
    
    def authorize_payin(self, transaction_ref: str, otp_code: str) -> Dict[str, Any]:
        """
        Autoriser un paiement avec le code OTP
        
        Args:
            transaction_ref: Référence de la transaction
            otp_code: Code OTP reçu par SMS
            
        Returns:
            Réponse d'autorisation
        """
        data = {
            'transaction_ref': transaction_ref,
            'code': otp_code
        }
        
        return self._make_request('authorize', 'POST', data)
    
    def initiate_payout(self, payout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initier un remboursement (payout)
        
        Args:
            payout_data: Données du remboursement
            
        Returns:
            Réponse du payout
        """
        required_fields = [
            'transaction_amount', 'transaction_currency', 'transaction_reason',
            'transaction_operator', 'app_transaction_ref', 'customer_phone_number',
            'customer_name', 'customer_email'
        ]
        
        for field in required_fields:
            if field not in payout_data:
                raise MyCoolPayError(f"Champ requis manquant: {field}")
        
        return self._make_request('payout', 'POST', payout_data)
    
    def check_transaction_status(self, transaction_ref: str) -> Dict[str, Any]:
        """
        Vérifier le statut d'une transaction
        
        Args:
            transaction_ref: Référence de la transaction
            
        Returns:
            Statut de la transaction (PENDING, SUCCESS, CANCELED, FAILED)
        """
        return self._make_request(f'status/{transaction_ref}', 'GET')
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Obtenir le solde du compte
        
        Returns:
            Solde du compte My-CoolPay
        """
        return self._make_request('balance', 'GET')
    
    def verify_callback_ip(self, ip_address: str) -> bool:
        """
        Vérifier si l'IP provient de My-CoolPay
        
        Args:
            ip_address: Adresse IP à vérifier
            
        Returns:
            True si l'IP est valide
        """
        # IPs autorisées pour My-CoolPay (à adapter selon la doc officielle)
        allowed_ips = [
            '185.199.109.0/24',  # Exemple
            '185.199.110.0/24',  # À remplacer par les vraies IPs
        ]
        
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            
            for allowed_range in allowed_ips:
                if ip in ipaddress.ip_network(allowed_range):
                    return True
                    
        except ValueError:
            logger.warning(f"Adresse IP invalide: {ip_address}")
            
        return False
    
    def verify_callback_signature(self, callback_data: Dict[str, Any]) -> bool:
        """
        Vérifier la signature du callback
        
        Args:
            callback_data: Données du callback
            
        Returns:
            True si la signature est valide
        """
        if 'signature' not in callback_data:
            return False
            
        signature = callback_data.pop('signature')
        
        # Créer la chaîne à signer
        sorted_data = sorted(callback_data.items())
        data_string = '&'.join([f"{k}={v}" for k, v in sorted_data])
        
        # Calculer la signature HMAC
        expected_signature = hmac.new(
            self.private_key.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_subscription_payment(self, user, subscription_plan, payment_method: str) -> Tuple[bool, str, Dict]:
        """
        Traiter un paiement d'abonnement
        
        Args:
            user: Utilisateur
            subscription_plan: Plan d'abonnement
            payment_method: Méthode de paiement
            
        Returns:
            (success, message, payment_data)
        """
        try:
            # Créer l'enregistrement de paiement
            payment = Payment.objects.create(
                user=user,
                amount=subscription_plan.price,
                currency=subscription_plan.currency or 'XAF',
                description=f"Abonnement {subscription_plan.name}",
                payment_method=payment_method,
                status=PaymentStatus.PENDING,
                metadata={
                    'subscription_plan_id': subscription_plan.id,
                    'plan_name': subscription_plan.name,
                    'duration_months': subscription_plan.duration_months
                }
            )
            
            # Préparer les données pour My-CoolPay
            payment_data = {
                'transaction_amount': float(payment.amount),
                'transaction_currency': payment.currency,
                'transaction_reason': payment.description,
                'app_transaction_ref': str(payment.id),
                'customer_phone_number': user.phone_number or '000000000',
                'customer_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'customer_email': user.email,
                'customer_lang': 'fr'
            }
            
            # Créer le paylink
            response = self.create_paylink(payment_data)
            
            # Mettre à jour le paiement avec la référence My-CoolPay
            payment.external_reference = response.get('transaction_ref')
            payment.payment_url = response.get('payment_url')
            payment.save()
            
            return True, "Lien de paiement créé avec succès", {
                'payment_id': payment.id,
                'payment_url': response.get('payment_url'),
                'transaction_ref': response.get('transaction_ref')
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paiement d'abonnement: {str(e)}")
            return False, f"Erreur: {str(e)}", {}
    
    def handle_payment_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        Traiter un callback de paiement
        
        Args:
            callback_data: Données du callback
            
        Returns:
            True si traité avec succès
        """
        try:
            # Vérifier la signature
            if not self.verify_callback_signature(callback_data.copy()):
                logger.warning("Signature de callback invalide")
                return False
            
            transaction_ref = callback_data.get('transaction_ref')
            app_transaction_ref = callback_data.get('app_transaction_ref')
            status = callback_data.get('transaction_status')
            
            if not all([transaction_ref, app_transaction_ref, status]):
                logger.warning("Données de callback incomplètes")
                return False
            
            # Trouver le paiement
            try:
                payment = Payment.objects.get(id=app_transaction_ref)
            except Payment.DoesNotExist:
                logger.warning(f"Paiement non trouvé: {app_transaction_ref}")
                return False
            
            # Mettre à jour le statut
            if status == 'SUCCESS':
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = timezone.now()
                
                # Traiter l'abonnement si c'est un paiement d'abonnement
                if 'subscription_plan_id' in payment.metadata:
                    self._process_subscription_activation(payment)
                    
            elif status == 'FAILED':
                payment.status = PaymentStatus.FAILED
            elif status == 'CANCELED':
                payment.status = PaymentStatus.CANCELLED
            
            payment.external_reference = transaction_ref
            payment.save()
            
            logger.info(f"Callback traité: Payment {payment.id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du callback: {str(e)}")
            return False
    
    def _process_subscription_activation(self, payment):
        """
        Activer un abonnement après paiement réussi
        
        Args:
            payment: Paiement complété
        """
        try:
            plan_id = payment.metadata.get('subscription_plan_id')
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Désactiver l'abonnement actuel s'il existe
            UserSubscription.objects.filter(
                user=payment.user, 
                is_active=True
            ).update(is_active=False, end_date=timezone.now())
            
            # Créer le nouvel abonnement
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=plan.duration_months * 30)
            
            subscription = UserSubscription.objects.create(
                user=payment.user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                payment=payment
            )
            
            logger.info(f"Abonnement activé: User {payment.user.id} -> Plan {plan.name}")
            
            # Envoyer une notification
            from apps.notifications.services.notification_service import NotificationService
            
            NotificationService.create_from_template(
                template_code='subscription_activated',
                recipient=payment.user,
                context_data={
                    'plan_name': plan.name,
                    'end_date': end_date.strftime('%d/%m/%Y')
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de l'abonnement: {str(e)}")


# Service global pour l'application
def get_mycoolpay_service() -> MyCoolPayService:
    """
    Obtenir une instance du service My-CoolPay
    
    Returns:
        Instance configurée du service
    """
    # Utiliser sandbox en mode DEBUG
    sandbox = getattr(settings, 'DEBUG', True)
    return MyCoolPayService(sandbox=sandbox) 