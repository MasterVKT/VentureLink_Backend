"""
Tests pour les modèles de paiement.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.payments.models import Payment, Refund


User = get_user_model()


class PaymentModelTest(TestCase):
    """Tests pour le modèle Payment."""
    
    def setUp(self):
        """Préparation des tests."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            currency='EUR',
            description='Test payment',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            status=Payment.PaymentStatus.PENDING,
            external_payment_id='test_payment_123',
            external_checkout_url='https://mycoolpay.com/checkout/test_payment_123'
        )
    
    def test_payment_creation(self):
        """Vérifie que le paiement est créé correctement."""
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.amount, Decimal('100.00'))
        self.assertEqual(self.payment.currency, 'EUR')
        self.assertEqual(self.payment.description, 'Test payment')
        self.assertEqual(self.payment.payment_type, Payment.PaymentType.SUBSCRIPTION)
        self.assertEqual(self.payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(self.payment.external_payment_id, 'test_payment_123')
        self.assertEqual(self.payment.external_checkout_url, 'https://mycoolpay.com/checkout/test_payment_123')
        self.assertFalse(self.payment.is_test)
    
    def test_payment_string_representation(self):
        """Vérifie la représentation sous forme de chaîne du paiement."""
        expected_string = f"Paiement de 100.00 EUR - En attente"
        self.assertEqual(str(self.payment), expected_string)
    
    def test_is_completed_property(self):
        """Vérifie la propriété is_completed."""
        self.assertFalse(self.payment.is_completed)
        
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.save()
        
        self.assertTrue(self.payment.is_completed)
    
    def test_is_refunded_property(self):
        """Vérifie la propriété is_refunded."""
        self.assertFalse(self.payment.is_refunded)
        
        self.payment.status = Payment.PaymentStatus.REFUNDED
        self.payment.save()
        
        self.assertTrue(self.payment.is_refunded)
        
        self.payment.status = Payment.PaymentStatus.PARTIALLY_REFUNDED
        self.payment.save()
        
        self.assertTrue(self.payment.is_refunded)
    
    def test_can_be_refunded_property(self):
        """Vérifie la propriété can_be_refunded."""
        self.assertFalse(self.payment.can_be_refunded)
        
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.save()
        
        self.assertTrue(self.payment.can_be_refunded)
        
        self.payment.status = Payment.PaymentStatus.REFUNDED
        self.payment.save()
        
        self.assertFalse(self.payment.can_be_refunded)


class RefundModelTest(TestCase):
    """Tests pour le modèle Refund."""
    
    def setUp(self):
        """Préparation des tests."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            currency='EUR',
            description='Test payment',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            status=Payment.PaymentStatus.COMPLETED,
            external_payment_id='test_payment_123',
            completed_at=timezone.now()
        )
        
        self.refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            currency='EUR',
            status=Refund.RefundStatus.PENDING,
            external_refund_id='test_refund_123',
            reason='Customer request'
        )
    
    def test_refund_creation(self):
        """Vérifie que le remboursement est créé correctement."""
        self.assertEqual(self.refund.payment, self.payment)
        self.assertEqual(self.refund.amount, Decimal('50.00'))
        self.assertEqual(self.refund.currency, 'EUR')
        self.assertEqual(self.refund.status, Refund.RefundStatus.PENDING)
        self.assertEqual(self.refund.external_refund_id, 'test_refund_123')
        self.assertEqual(self.refund.reason, 'Customer request')
    
    def test_refund_string_representation(self):
        """Vérifie la représentation sous forme de chaîne du remboursement."""
        expected_string = f"Remboursement de 50.00 EUR - En attente"
        self.assertEqual(str(self.refund), expected_string)
    
    def test_is_completed_property(self):
        """Vérifie la propriété is_completed."""
        self.assertFalse(self.refund.is_completed)
        
        self.refund.status = Refund.RefundStatus.COMPLETED
        self.refund.save()
        
        self.assertTrue(self.refund.is_completed) 