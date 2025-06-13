"""
Tests d'intégration pour l'application investments avec My-CoolPay.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.investments.models import (
    Investment, InvestmentPayment, InvestmentHistory
)
from apps.payments.models import Payment, Refund
from apps.payments.services import PaymentService


class InvestmentPaymentIntegrationTest(TestCase):
    """Tests d'intégration entre les investissements et My-CoolPay."""

    def setUp(self):
        # Créer des utilisateurs
        self.entrepreneur = User.objects.create_user(
            email='entrepreneur@venturelink.com',
            password='testpassword',
            user_type='ENTREPRENEUR'
        )
        
        self.investor = User.objects.create_user(
            email='investor@venturelink.com',
            password='testpassword',
            user_type='INVESTOR'
        )
        
        # Créer une catégorie
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        
        # Créer un projet
        self.project = Project.objects.create(
            creator=self.entrepreneur,
            title='Projet de test',
            short_description='Une description courte du projet de test',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category,
            is_draft=False  # Projet publié
        )
        
        # Créer un investissement
        self.investment = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('15000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_EQUITY,
            equity_percentage=Decimal('5.00'),
            status=Investment.STATUS_PENDING
        )
        
        # Initialiser le client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.investor)

    @patch('apps.payments.services.payment_service.MyCoolPayService')
    def test_create_investment_payment_with_my_coolpay(self, mock_my_coolpay):
        """Test l'intégration entre un paiement d'investissement et My-CoolPay."""
        # Configurer le mock pour simuler une réponse de My-CoolPay
        mock_instance = mock_my_coolpay.return_value
        mock_instance.create_payment.return_value = {
            'payment_id': 'mcp_pay_123456789',
            'status': 'pending',
            'checkout_url': 'https://checkout.mycoolpay.com/p/123456789'
        }
        
        # URL pour créer un paiement
        url = reverse('investment-create-payment', kwargs={'pk': self.investment.id})
        
        payment_data = {
            'amount': '15000.00',
            'currency': 'EUR',
            'payment_method': InvestmentPayment.METHOD_CREDIT_CARD,
            'return_url': 'https://venturelink.com/investments/success',
            'cancel_url': 'https://venturelink.com/investments/cancel'
        }
        
        response = self.client.post(url, payment_data, format='json')
        
        # Vérifier que la réponse est correcte
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('checkout_url', response.data)
        self.assertEqual(response.data['checkout_url'], 'https://checkout.mycoolpay.com/p/123456789')
        
        # Vérifier que le service My-CoolPay a été appelé correctement
        mock_instance.create_payment.assert_called_once()
        
        # Vérifier que le paiement a été créé dans la base de données
        self.assertTrue(InvestmentPayment.objects.filter(
            investment=self.investment,
            amount=Decimal('15000.00'),
            transaction_id='mcp_pay_123456789'
        ).exists())

    @patch('apps.payments.services.payment_service.MyCoolPayService')
    def test_payment_webhook_updates_investment_status(self, mock_my_coolpay):
        """Test que le webhook de My-CoolPay met à jour correctement l'investissement."""
        # Créer un paiement d'investissement lié à My-CoolPay
        payment = InvestmentPayment.objects.create(
            investment=self.investment,
            amount=Decimal('15000.00'),
            currency='EUR',
            payment_method=InvestmentPayment.METHOD_CREDIT_CARD,
            transaction_id='mcp_pay_123456789',
            status=InvestmentPayment.STATUS_PENDING
        )
        
        # Configurer le mock pour vérifier la signature du webhook
        mock_instance = mock_my_coolpay.return_value
        mock_instance.verify_webhook_signature.return_value = True
        
        # URL du webhook My-CoolPay
        url = reverse('mycoolpay-webhook')
        
        # Données simulées d'un webhook de paiement réussi
        webhook_data = {
            'event_type': 'payment.completed',
            'payment_id': 'mcp_pay_123456789',
            'status': 'completed',
            'amount': '15000.00',
            'currency': 'EUR',
            'metadata': {
                'payment_type': 'investment',
                'investment_id': str(self.investment.id)
            },
            'timestamp': '2023-08-01T12:00:00Z',
            'signature': 'valid_signature'
        }
        
        # Envoyer le webhook
        response = self.client.post(
            url, 
            webhook_data, 
            format='json',
            HTTP_X_MYCOOLPAY_SIGNATURE='valid_signature'
        )
        
        # Vérifier que le webhook est traité avec succès
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le paiement a été mis à jour
        payment.refresh_from_db()
        self.assertEqual(payment.status, InvestmentPayment.STATUS_COMPLETED)
        
        # Vérifier que l'investissement a été mis à jour
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, Investment.STATUS_APPROVED)

    @patch('apps.payments.services.payment_service.MyCoolPayService')
    def test_refund_investment_payment(self, mock_my_coolpay):
        """Test le remboursement d'un paiement d'investissement via My-CoolPay."""
        # Créer un paiement d'investissement complété
        payment = InvestmentPayment.objects.create(
            investment=self.investment,
            amount=Decimal('15000.00'),
            currency='EUR',
            payment_method=InvestmentPayment.METHOD_CREDIT_CARD,
            transaction_id='mcp_pay_123456789',
            status=InvestmentPayment.STATUS_COMPLETED
        )
        
        # Mettre l'investissement en statut approuvé
        self.investment.status = Investment.STATUS_APPROVED
        self.investment.save()
        
        # Configurer le mock pour simuler un remboursement réussi
        mock_instance = mock_my_coolpay.return_value
        mock_instance.create_refund.return_value = {
            'refund_id': 'mcp_ref_123456789',
            'status': 'completed',
            'amount': '15000.00'
        }
        
        # URL pour demander un remboursement
        url = reverse('investment-refund', kwargs={'pk': self.investment.id})
        
        # Connecter l'entrepreneur pour effectuer le remboursement
        self.client.force_authenticate(user=self.entrepreneur)
        
        refund_data = {
            'reason': 'Projet annulé',
            'amount': '15000.00'
        }
        
        response = self.client.post(url, refund_data, format='json')
        
        # Vérifier que la réponse est correcte
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le service My-CoolPay a été appelé correctement
        mock_instance.create_refund.assert_called_once()
        
        # Vérifier que le paiement a été mis à jour
        payment.refresh_from_db()
        self.assertEqual(payment.status, InvestmentPayment.STATUS_REFUNDED)
        
        # Vérifier que l'investissement a été annulé
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, Investment.STATUS_CANCELLED)

    def test_currency_conversion_for_investment(self):
        """Test la conversion de devises pour les montants d'investissement."""
        # Créer un investissement dans une devise différente
        investment_usd = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('18000.00'),
            currency='USD',  # Devise différente de EUR
            investment_type=Investment.TYPE_EQUITY,
            equity_percentage=Decimal('5.00'),
            status=Investment.STATUS_PENDING
        )
        
        # URL pour obtenir les détails de l'investissement avec conversion
        url = reverse('investment-detail', kwargs={'pk': investment_usd.id})
        
        # Ajouter le paramètre de devise pour la conversion
        response = self.client.get(f"{url}?currency=EUR")
        
        # Vérifier que la réponse inclut le montant converti
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amount_converted', response.data)
        self.assertIn('currency_converted', response.data)
        self.assertEqual(response.data['currency_converted'], 'EUR') 