"""
Service d'intégration avec l'API de paiement My-CoolPay.
"""
import logging
import json
import uuid
import requests
from typing import Dict, Any, Optional, Union, List
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MyCoolPayService:
    """
    Service pour intégrer l'API de paiement My-CoolPay.
    
    Cette classe fournit les méthodes pour interagir avec l'API My-CoolPay,
    permettant de créer et gérer les paiements, vérifier leur statut, etc.
    """
    
    # Durée de mise en cache des données (1 heure)
    CACHE_TIMEOUT = 60 * 60
    
    def __init__(self):
        """
        Initialise le service de paiement avec les configurations.
        """
        # Déterminer si on est en mode sandbox ou production
        self.sandbox_mode = getattr(settings, 'PAYMENT_SANDBOX_MODE', True)
        
        # Récupérer les clés API appropriées
        if self.sandbox_mode:
            self.api_key = getattr(settings, 'MYCOOLPAY_SANDBOX_API_KEY', '')
            self.webhook_secret = getattr(settings, 'MYCOOLPAY_SANDBOX_WEBHOOK_SECRET', '')
            self.api_base_url = 'https://sandbox-api.mycoolpay.com/v1/'
        else:
            self.api_key = getattr(settings, 'MYCOOLPAY_PRODUCTION_API_KEY', '')
            self.webhook_secret = getattr(settings, 'MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET', '')
            self.api_base_url = 'https://api.mycoolpay.com/v1/'
        
        # Vérifier que la clé API est configurée
        if not self.api_key:
            logger.warning("API key My-CoolPay non configurée. Les paiements ne fonctionneront pas.")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête à l'API My-CoolPay.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, etc.)
            endpoint: Point d'entrée de l'API (sans l'URL de base)
            data: Données à envoyer (pour POST, PUT)
            params: Paramètres de requête (pour GET)
            
        Returns:
            Dict: Réponse de l'API
            
        Raises:
            Exception: Si la requête échoue
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                params=params if params else None,
                timeout=30
            )
            
            # Vérifier si la requête a réussi
            response.raise_for_status()
            
            # Parser la réponse JSON
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête à My-CoolPay: {str(e)}")
            # Si la réponse contient des détails d'erreur, les logger
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Détails de l'erreur My-CoolPay: {json.dumps(error_data)}")
                except ValueError:
                    logger.error(f"Corps de la réponse: {e.response.text}")
            
            # Reraise l'exception pour que l'appelant puisse la gérer
            raise
    
    def create_payment(self, amount: Union[Decimal, float], currency: str, 
                       description: str, customer_email: str, 
                       metadata: Optional[Dict[str, str]] = None,
                       success_url: Optional[str] = None,
                       cancel_url: Optional[str] = None,
                       statement_descriptor: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée un paiement via My-CoolPay.
        
        Args:
            amount: Montant à payer
            currency: Code de la devise (EUR, USD, etc.)
            description: Description du paiement
            customer_email: Email du client
            metadata: Données supplémentaires à stocker
            success_url: URL de redirection après paiement réussi
            cancel_url: URL de redirection en cas d'annulation
            statement_descriptor: Description qui apparaîtra sur le relevé bancaire
            
        Returns:
            Dict: Détails du paiement créé, incluant l'ID de paiement et l'URL de paiement
        """
        # Préparer les données
        payment_data = {
            'amount': int(float(amount) * 100),  # Convertir en centimes
            'currency': currency.upper(),
            'description': description,
            'customer_email': customer_email,
            'idempotency_key': str(uuid.uuid4()),  # Éviter les doublons
            'metadata': metadata or {},
        }
        
        # Ajouter les URLs de redirection si fournies
        if success_url:
            payment_data['success_url'] = success_url
        if cancel_url:
            payment_data['cancel_url'] = cancel_url
        if statement_descriptor:
            payment_data['statement_descriptor'] = statement_descriptor[:22]  # Limite de 22 caractères
        
        # Faire la requête à l'API
        response = self._make_request('POST', 'payments/create', data=payment_data)
        
        # Transformer la réponse pour notre utilisation
        return {
            'payment_id': response.get('id'),
            'payment_url': response.get('checkout_url'),
            'status': response.get('status'),
            'amount': float(response.get('amount', 0)) / 100,  # Convertir en unités monétaires
            'currency': response.get('currency'),
            'created_at': response.get('created_at'),
            'expires_at': response.get('expires_at'),
            'raw_response': response
        }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un paiement.
        
        Args:
            payment_id: Identifiant du paiement
            
        Returns:
            Dict: Détails du paiement, incluant son statut
        """
        response = self._make_request('GET', f'payments/{payment_id}')
        
        # Transformer la réponse pour notre utilisation
        return {
            'payment_id': response.get('id'),
            'status': response.get('status'),
            'amount': float(response.get('amount', 0)) / 100,
            'currency': response.get('currency'),
            'customer_email': response.get('customer_email'),
            'description': response.get('description'),
            'created_at': response.get('created_at'),
            'updated_at': response.get('updated_at'),
            'completed_at': response.get('completed_at'),
            'metadata': response.get('metadata', {}),
            'raw_response': response
        }
    
    def refund_payment(self, payment_id: str, amount: Optional[Union[Decimal, float]] = None, 
                       reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Rembourse un paiement, entièrement ou partiellement.
        
        Args:
            payment_id: Identifiant du paiement
            amount: Montant à rembourser (si non spécifié, rembourse la totalité)
            reason: Raison du remboursement
            
        Returns:
            Dict: Détails du remboursement
        """
        refund_data = {}
        
        if amount is not None:
            refund_data['amount'] = int(float(amount) * 100)  # Convertir en centimes
        if reason:
            refund_data['reason'] = reason
        
        response = self._make_request('POST', f'payments/{payment_id}/refund', data=refund_data)
        
        # Transformer la réponse pour notre utilisation
        return {
            'refund_id': response.get('id'),
            'payment_id': response.get('payment_id'),
            'status': response.get('status'),
            'amount': float(response.get('amount', 0)) / 100,
            'currency': response.get('currency'),
            'created_at': response.get('created_at'),
            'raw_response': response
        }
    
    def list_payments(self, limit: int = 20, starting_after: Optional[str] = None, 
                     status: Optional[str] = None, customer_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Liste les paiements avec des filtres optionnels.
        
        Args:
            limit: Nombre maximum de paiements à retourner
            starting_after: ID du paiement après lequel commencer
            status: Filtrer par statut
            customer_email: Filtrer par email client
            
        Returns:
            Dict: Liste des paiements et pagination
        """
        params = {'limit': limit}
        
        if starting_after:
            params['starting_after'] = starting_after
        if status:
            params['status'] = status
        if customer_email:
            params['customer_email'] = customer_email
        
        response = self._make_request('GET', 'payments', params=params)
        
        # Transformer la réponse pour notre utilisation
        payments = []
        for payment in response.get('data', []):
            payments.append({
                'payment_id': payment.get('id'),
                'status': payment.get('status'),
                'amount': float(payment.get('amount', 0)) / 100,
                'currency': payment.get('currency'),
                'customer_email': payment.get('customer_email'),
                'description': payment.get('description'),
                'created_at': payment.get('created_at'),
            })
        
        return {
            'payments': payments,
            'has_more': response.get('has_more', False),
            'total_count': response.get('total_count', 0),
            'next_page': response.get('next_page', None),
        }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Vérifie la signature d'un webhook My-CoolPay.
        
        Args:
            payload: Corps de la requête webhook (chaîne JSON)
            signature: Signature fournie dans l'en-tête X-MyCoolPay-Signature
            
        Returns:
            bool: True si la signature est valide, False sinon
        """
        import hmac
        import hashlib
        
        # Si pas de secret webhook configuré, impossible de vérifier
        if not self.webhook_secret:
            logger.warning("Webhook secret non configuré, impossible de vérifier la signature")
            return False
        
        try:
            # Calculer la signature attendue
            expected_signature = hmac.new(
                key=self.webhook_secret.encode('utf-8'),
                msg=payload.encode('utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Comparer avec la signature reçue
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la signature webhook: {str(e)}")
            return False
    
    def parse_webhook_event(self, payload: str) -> Dict[str, Any]:
        """
        Parse le contenu d'un webhook My-CoolPay.
        
        Args:
            payload: Corps de la requête webhook (chaîne JSON)
            
        Returns:
            Dict: Données de l'événement webhook
        """
        try:
            event_data = json.loads(payload)
            
            return {
                'event_id': event_data.get('id'),
                'event_type': event_data.get('type'),
                'created_at': event_data.get('created_at'),
                'data': event_data.get('data', {}),
                'raw_event': event_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors du parsing du webhook: {str(e)}")
            raise ValueError("Impossible de parser le contenu du webhook") 