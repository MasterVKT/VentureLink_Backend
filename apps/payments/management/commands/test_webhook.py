"""
Commande pour tester les webhooks My-CoolPay en simulant des événements.
"""
import json
import hmac
import hashlib
import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.urls import reverse


class Command(BaseCommand):
    """
    Commande pour tester les webhooks My-CoolPay en simulant des événements.
    
    Usage:
        python manage.py test_webhook payment.success
        python manage.py test_webhook payment.failed
        python manage.py test_webhook payment.refunded
    """
    
    help = 'Teste les webhooks My-CoolPay en simulant des événements'
    
    def add_arguments(self, parser):
        """Ajouter les arguments de la commande."""
        parser.add_argument('event_type', type=str, help='Type d\'événement à simuler')
        parser.add_argument('--transaction-ref', type=str, dest='transaction_ref',
                            help='Référence de transaction (optionnel)')
        parser.add_argument('--app-transaction-ref', type=str, dest='app_transaction_ref',
                            help='Référence de transaction de l\'application (optionnel)')
        parser.add_argument('--url', type=str, help='URL du webhook (par défaut: localhost)')
    
    def handle(self, *args, **options):
        """Exécuter la commande."""
        event_type = options['event_type']
        transaction_ref = options.get('transaction_ref') or 'test_transaction_123'
        app_transaction_ref = options.get('app_transaction_ref')
        
        # Construire l'URL du webhook
        webhook_url = options.get('url')
        if not webhook_url:
            # URL par défaut en local
            webhook_url = 'http://localhost:8000/api/v1/payments/mycoolpay/webhook/'
        
        # Obtenir les données d'événement
        event_data = self._get_event_data(event_type, transaction_ref, app_transaction_ref)
        
        # Signer la requête
        webhook_secret = settings.MYCOOLPAY_SANDBOX_WEBHOOK_SECRET
        payload = json.dumps(event_data)
        signature = hmac.new(
            key=webhook_secret.encode(),
            msg=payload.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Envoyer la requête webhook
        headers = {
            'Content-Type': 'application/json',
            'X-MyCoolPay-Signature': signature
        }
        
        self.stdout.write(f"Envoi d'un événement webhook de type '{event_type}' à {webhook_url}")
        
        try:
            response = requests.post(webhook_url, data=payload, headers=headers, timeout=10)
            
            # Afficher la réponse
            self.stdout.write(f"Statut de la réponse: {response.status_code}")
            self.stdout.write(f"Contenu de la réponse: {response.text}")
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Webhook traité avec succès!'))
            else:
                self.stdout.write(self.style.ERROR(f"Erreur lors du traitement du webhook: {response.status_code}"))
                
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Erreur de connexion: {str(e)}"))
    
    def _get_event_data(self, event_type, transaction_ref, app_transaction_ref=None):
        """
        Obtenir les données d'événement pour un type spécifique.
        
        Args:
            event_type: Type d'événement
            transaction_ref: Référence de transaction
            app_transaction_ref: Référence de transaction de l'application
            
        Returns:
            dict: Données d'événement
        """
        base_data = {
            'event_type': event_type,
            'transaction_ref': transaction_ref,
            'transaction_date': '2023-12-20T10:30:00Z',
        }
        
        if app_transaction_ref:
            base_data['app_transaction_ref'] = app_transaction_ref
        
        if event_type == 'payment.success':
            base_data.update({
                'transaction_details': {
                    'amount': 100.00,
                    'currency': 'EUR',
                    'payment_method': 'card'
                }
            })
        elif event_type == 'payment.failed':
            base_data.update({
                'error_code': 'payment_failed',
                'error_details': 'Paiement refusé par la banque'
            })
        elif event_type == 'payment.refunded':
            base_data.update({
                'refund_ref': f'refund_{transaction_ref}',
                'refund_amount': 100.00,
                'refund_reason': 'Remboursement demandé par le client'
            })
        elif event_type == 'subscription.created':
            base_data.update({
                'subscription_ref': f'sub_{transaction_ref}',
                'subscription_details': {
                    'plan_id': 'premium_monthly',
                    'start_date': '2023-12-20T10:30:00Z',
                    'end_date': '2024-01-20T10:30:00Z'
                }
            })
        elif event_type == 'subscription.cancelled':
            base_data.update({
                'subscription_ref': f'sub_{transaction_ref}',
                'cancellation_reason': 'Annulation demandée par le client',
                'cancellation_date': '2023-12-20T10:30:00Z'
            })
        elif event_type == 'subscription.renewed':
            base_data.update({
                'subscription_ref': f'sub_{transaction_ref}',
                'renewal_transaction_ref': f'renewal_{transaction_ref}',
                'renewal_date': '2023-12-20T10:30:00Z',
                'next_renewal_date': '2024-01-20T10:30:00Z'
            })
        
        return base_data 