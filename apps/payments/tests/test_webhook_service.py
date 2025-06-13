"""
Tests pour le service de webhook My-CoolPay.
"""
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.payments.models import Payment, Refund
from apps.payments.services.webhook_service import WebhookService

User = get_user_model()


class WebhookServiceTest(TestCase):
    """Tests pour le service de webhook My-CoolPay."""
    
    def setUp(self):
        """Initialiser les données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Créer un paiement de test
        self.payment = Payment.objects.create(
            user=self.user,
            amount=100.00,
            currency='EUR',
            description='Test payment',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            external_payment_id='test-payment-123',
            status=Payment.PaymentStatus.PENDING
        )
        
        # Données d'événement webhook de test
        self.payment_success_event = {
            'event_type': 'payment.success',
            'transaction_ref': 'test-payment-123',
            'transaction_date': '2023-10-15T14:30:00Z',
            'transaction_details': {
                'amount': 100.00,
                'currency': 'EUR',
                'payment_method': 'card'
            }
        }
        
        self.payment_failed_event = {
            'event_type': 'payment.failed',
            'transaction_ref': 'test-payment-123',
            'transaction_date': '2023-10-15T14:30:00Z',
            'error_code': 'card_declined',
            'error_details': 'Card was declined'
        }
        
        self.payment_refunded_event = {
            'event_type': 'payment.refunded',
            'transaction_ref': 'test-payment-123',
            'refund_ref': 'refund-123',
            'refund_amount': 100.00,
            'refund_reason': 'Customer requested'
        }
    
    def test_verify_signature(self):
        """Tester la vérification de la signature."""
        # Générer une signature valide
        secret = 'webhook-secret'
        payload = json.dumps({'test': 'data'})
        
        valid_signature = hmac.new(
            key=secret.encode(),
            msg=payload.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # La signature valide doit être vérifiée
        self.assertTrue(WebhookService.verify_signature(payload, valid_signature, secret))
        
        # Une signature invalide doit être rejetée
        invalid_signature = 'invalid-signature'
        self.assertFalse(WebhookService.verify_signature(payload, invalid_signature, secret))
        
        # Les entrées vides doivent être rejetées
        self.assertFalse(WebhookService.verify_signature('', valid_signature, secret))
        self.assertFalse(WebhookService.verify_signature(payload, '', secret))
        self.assertFalse(WebhookService.verify_signature(payload, valid_signature, ''))
    
    @patch('apps.notifications.services.notification_service.NotificationService.send_payment_success_notification')
    def test_handle_payment_success(self, mock_send_notification):
        """Tester le traitement d'un événement de paiement réussi."""
        # Traiter l'événement
        result = WebhookService._handle_payment_success(self.payment_success_event)
        
        # Vérifier le résultat
        self.assertTrue(result)
        
        # Recharger le paiement
        self.payment.refresh_from_db()
        
        # Vérifier que le statut a été mis à jour
        self.assertEqual(self.payment.status, Payment.PaymentStatus.COMPLETED)
        self.assertIsNotNone(self.payment.completed_at)
        
        # Vérifier que les métadonnées ont été mises à jour
        self.assertIn('transaction_details', self.payment.metadata)
        
        # Vérifier que la notification a été envoyée
        mock_send_notification.assert_called_once_with(self.payment)
    
    @patch('apps.notifications.services.notification_service.NotificationService.send_payment_failed_notification')
    def test_handle_payment_failed(self, mock_send_notification):
        """Tester le traitement d'un événement de paiement échoué."""
        # Traiter l'événement
        result = WebhookService._handle_payment_failed(self.payment_failed_event)
        
        # Vérifier le résultat
        self.assertTrue(result)
        
        # Recharger le paiement
        self.payment.refresh_from_db()
        
        # Vérifier que le statut a été mis à jour
        self.assertEqual(self.payment.status, Payment.PaymentStatus.FAILED)
        
        # Vérifier que les métadonnées ont été mises à jour
        self.assertIn('error_details', self.payment.metadata)
        self.assertEqual(self.payment.metadata['error_code'], 'card_declined')
        
        # Vérifier que la notification a été envoyée
        mock_send_notification.assert_called_once_with(self.payment)
    
    @patch('apps.notifications.services.notification_service.NotificationService.send_refund_notification')
    def test_handle_payment_refunded(self, mock_send_notification):
        """Tester le traitement d'un événement de paiement remboursé."""
        # Mettre le paiement en état complété
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.completed_at = timezone.now()
        self.payment.save()
        
        # Traiter l'événement
        result = WebhookService._handle_payment_refunded(self.payment_refunded_event)
        
        # Vérifier le résultat
        self.assertTrue(result)
        
        # Recharger le paiement
        self.payment.refresh_from_db()
        
        # Vérifier que le statut a été mis à jour
        self.assertEqual(self.payment.status, Payment.PaymentStatus.REFUNDED)
        
        # Vérifier qu'un remboursement a été créé
        refund = Refund.objects.filter(payment=self.payment).first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.status, Refund.RefundStatus.COMPLETED)
        self.assertEqual(float(refund.amount), 100.00)
        self.assertEqual(refund.currency, 'EUR')
        self.assertEqual(refund.external_refund_id, 'refund-123')
        
        # Vérifier que la notification a été envoyée
        mock_send_notification.assert_called_once()
    
    def test_process_webhook_event(self):
        """Tester le traitement d'un événement webhook."""
        # Mocker les méthodes de traitement
        with patch.object(WebhookService, '_handle_payment_success', return_value=True) as mock_success:
            # Traiter l'événement de succès
            result = WebhookService.process_webhook_event(self.payment_success_event)
            
            # Vérifier que la méthode appropriée a été appelée
            self.assertTrue(result)
            mock_success.assert_called_once_with(self.payment_success_event)
        
        # Événement inconnu
        unknown_event = {'event_type': 'unknown.event'}
        result = WebhookService.process_webhook_event(unknown_event)
        self.assertFalse(result)
        
        # Événement sans type
        invalid_event = {'data': 'no_event_type'}
        result = WebhookService.process_webhook_event(invalid_event)
        self.assertFalse(result) 