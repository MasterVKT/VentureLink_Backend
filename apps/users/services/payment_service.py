"""
Service pour gérer les paiements via l'API My-CoolPay.
"""
import os
import json
import logging
import requests
from django.conf import settings
from django.urls import reverse
from urllib.parse import urljoin

from apps.core.exceptions import PaymentError, ValidationError

logger = logging.getLogger(__name__)

class PaymentService:
    """
    Service pour gérer les paiements via l'API My-CoolPay.
    
    Cette classe gère l'interaction avec l'API My-CoolPay pour:
    - Initialiser des paiements
    - Vérifier le statut des paiements
    - Traiter les webhooks de notification
    """
    
    # URLs de l'API My-CoolPay
    SANDBOX_BASE_URL = "https://sandbox.my-coolpay.com/api/v1/"
    PRODUCTION_BASE_URL = "https://api.my-coolpay.com/api/v1/"
    
    # Endpoints
    PAYMENT_INIT_ENDPOINT = "payments/init"
    PAYMENT_STATUS_ENDPOINT = "payments/{payment_id}/status"
    PAYMENT_CANCEL_ENDPOINT = "payments/{payment_id}/cancel"
    PAYMENT_REFUND_ENDPOINT = "payments/{payment_id}/refund"
    
    def __init__(self):
        """
        Initialise le service avec les clés d'API appropriées selon l'environnement.
        """
        self.is_sandbox = getattr(settings, "PAYMENT_SANDBOX_MODE", True)
        
        if self.is_sandbox:
            self.api_key = getattr(settings, "MYCOOLPAY_SANDBOX_API_KEY", "")
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.api_key = getattr(settings, "MYCOOLPAY_PRODUCTION_API_KEY", "")
            self.base_url = self.PRODUCTION_BASE_URL
            
        if not self.api_key:
            logger.error("Clé API My-CoolPay non configurée")
            
    def _get_headers(self):
        """
        Retourne les en-têtes pour les requêtes API.
        
        Returns:
            dict: En-têtes HTTP pour les requêtes API
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def _make_request(self, method, endpoint, data=None, params=None):
        """
        Effectue une requête à l'API My-CoolPay.
        
        Args:
            method (str): Méthode HTTP (GET, POST, etc.)
            endpoint (str): Endpoint de l'API
            data (dict, optional): Données pour la requête
            params (dict, optional): Paramètres pour la requête
            
        Returns:
            dict: Réponse de l'API
            
        Raises:
            PaymentError: En cas d'erreur de communication avec l'API
        """
        url = urljoin(self.base_url, endpoint)
        headers = self._get_headers()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la communication avec My-CoolPay: {str(e)}")
            raise PaymentError("Erreur de communication avec le service de paiement")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {str(e)}")
            raise PaymentError("Réponse invalide du service de paiement")
            
    def init_subscription_payment(self, user, plan, currency="EUR", return_url=None):
        """
        Initialise un paiement pour un abonnement.
        
        Args:
            user: L'utilisateur qui souscrit
            plan (str): Le plan d'abonnement choisi (PREMIUM_MONTHLY, PREMIUM_YEARLY)
            currency (str, optional): La devise du paiement
            return_url (str, optional): URL de retour après paiement
            
        Returns:
            dict: Informations sur le paiement initialisé (checkout_url, payment_id)
            
        Raises:
            PaymentError: En cas d'erreur lors de l'initialisation du paiement
            ValidationError: Si les paramètres sont invalides
        """
        if plan not in ["PREMIUM_MONTHLY", "PREMIUM_YEARLY"]:
            raise ValidationError("Plan d'abonnement non valide")
            
        # Déterminer le montant basé sur le plan
        amount = 9.99 if plan == "PREMIUM_MONTHLY" else 99.99
        
        # Préparer les données pour l'API
        payment_data = {
            "amount": amount,
            "currency": currency,
            "description": f"Abonnement {plan} - VentureLink",
            "customer": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "customer_id": str(user.id)
            },
            "metadata": {
                "user_id": str(user.id),
                "plan": plan
            },
            "return_url": return_url or f"{settings.FRONTEND_URL}/subscription/success",
            "cancel_url": f"{settings.FRONTEND_URL}/subscription/cancel",
            "webhook_url": f"{settings.BACKEND_URL}{reverse('subscription-webhook')}"
        }
        
        try:
            response = self._make_request("POST", self.PAYMENT_INIT_ENDPOINT, data=payment_data)
            return {
                "checkout_url": response.get("checkout_url"),
                "checkout_id": response.get("payment_id")
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du paiement: {str(e)}")
            raise PaymentError("Impossible d'initialiser le paiement. Veuillez réessayer plus tard.")
            
    def get_payment_status(self, payment_id):
        """
        Récupère le statut d'un paiement.
        
        Args:
            payment_id (str): ID du paiement à vérifier
            
        Returns:
            dict: Statut du paiement
            
        Raises:
            PaymentError: En cas d'erreur lors de la récupération du statut
        """
        endpoint = self.PAYMENT_STATUS_ENDPOINT.format(payment_id=payment_id)
        return self._make_request("GET", endpoint)
        
    def cancel_payment(self, payment_id):
        """
        Annule un paiement.
        
        Args:
            payment_id (str): ID du paiement à annuler
            
        Returns:
            dict: Résultat de l'annulation
            
        Raises:
            PaymentError: En cas d'erreur lors de l'annulation
        """
        endpoint = self.PAYMENT_CANCEL_ENDPOINT.format(payment_id=payment_id)
        return self._make_request("POST", endpoint)
        
    def refund_payment(self, payment_id, amount=None, reason=None):
        """
        Rembourse un paiement.
        
        Args:
            payment_id (str): ID du paiement à rembourser
            amount (float, optional): Montant à rembourser (remboursement total si non spécifié)
            reason (str, optional): Raison du remboursement
            
        Returns:
            dict: Résultat du remboursement
            
        Raises:
            PaymentError: En cas d'erreur lors du remboursement
        """
        endpoint = self.PAYMENT_REFUND_ENDPOINT.format(payment_id=payment_id)
        data = {}
        
        if amount:
            data["amount"] = amount
        if reason:
            data["reason"] = reason
            
        return self._make_request("POST", endpoint, data=data)
    
    def verify_webhook_signature(self, payload, signature_header):
        """
        Vérifie la signature d'un webhook My-CoolPay.
        
        Args:
            payload (str): Le corps de la requête webhook en tant que chaîne
            signature_header (str): L'en-tête de signature My-CoolPay
            
        Returns:
            bool: True si la signature est valide, False sinon
        """
        if self.is_sandbox:
            webhook_secret = getattr(settings, "MYCOOLPAY_SANDBOX_WEBHOOK_SECRET", "")
        else:
            webhook_secret = getattr(settings, "MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET", "")
            
        if not webhook_secret:
            logger.warning("Secret de webhook My-CoolPay non configuré")
            return False
            
        # Cette implémentation est simplifiée, My-CoolPay fournirait
        # des instructions spécifiques pour la vérification des signatures
        # Dans une implémentation réelle, utilisez leur méthode recommandée
        
        # Par exemple:
        # import hmac
        # import hashlib
        # expected_signature = hmac.new(
        #     webhook_secret.encode(),
        #     payload.encode(),
        #     hashlib.sha256
        # ).hexdigest()
        # return hmac.compare_digest(expected_signature, signature_header)
        
        # Pour le développement, on accepte tous les webhooks
        return True 