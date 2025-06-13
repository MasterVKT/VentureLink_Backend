"""
Tests pour les vues de l'application investments.
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.investments.models import (
    Investment, InvestmentPayment,
    RepaymentSchedule, RepaymentTransaction
)


class InvestmentAPITest(TestCase):
    """Tests pour les API d'investissements."""

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
        
        self.other_investor = User.objects.create_user(
            email='other@venturelink.com',
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
        
        # Créer un paiement d'investissement
        self.payment = InvestmentPayment.objects.create(
            investment=self.investment,
            amount=Decimal('15000.00'),
            currency='EUR',
            payment_method=InvestmentPayment.METHOD_BANK_TRANSFER,
            transaction_id='TX123456789',
            status=InvestmentPayment.STATUS_PENDING
        )
        
        # Initialiser le client API
        self.client = APIClient()

    def test_list_investments_anonymous(self):
        """Test: un utilisateur anonyme ne peut pas voir les investissements."""
        url = reverse('investment-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_investments_investor(self):
        """Test: un investisseur peut voir ses propres investissements."""
        self.client.force_authenticate(user=self.investor)
        url = reverse('investment-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.investment.id))

    def test_list_investments_entrepreneur(self):
        """Test: un entrepreneur peut voir les investissements de ses projets."""
        self.client.force_authenticate(user=self.entrepreneur)
        url = reverse('investment-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.investment.id))

    def test_retrieve_investment(self):
        """Test: les parties impliquées peuvent voir un investissement spécifique."""
        url = reverse('investment-detail', kwargs={'pk': self.investment.id})
        
        # Utilisateur anonyme
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Investisseur propriétaire
        self.client.force_authenticate(user=self.investor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.investment.id))
        
        # Entrepreneur du projet
        self.client.force_authenticate(user=self.entrepreneur)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Autre investisseur non impliqué
        self.client.force_authenticate(user=self.other_investor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_investment(self):
        """Test: un investisseur peut créer un investissement."""
        self.client.force_authenticate(user=self.investor)
        url = reverse('investment-list')
        
        data = {
            'project': self.project.id,
            'amount': '10000.00',
            'currency': 'EUR',
            'investment_type': Investment.TYPE_EQUITY,
            'equity_percentage': '3.00',
            'note': 'Investissement test'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que l'investissement a été créé
        self.assertTrue(Investment.objects.filter(
            project=self.project,
            investor=self.investor,
            amount=Decimal('10000.00')
        ).exists())

    def test_cancel_investment(self):
        """Test: un investisseur peut annuler son investissement en attente."""
        self.client.force_authenticate(user=self.investor)
        url = reverse('investment-cancel', kwargs={'pk': self.investment.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que l'investissement a été annulé
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, Investment.STATUS_CANCELLED)

    def test_cannot_cancel_confirmed_investment(self):
        """Test: un investissement confirmé ne peut pas être annulé."""
        # Confirmer l'investissement
        self.investment.status = Investment.STATUS_CONFIRMED
        self.investment.confirmed_at = timezone.now()
        self.investment.save()
        
        self.client.force_authenticate(user=self.investor)
        url = reverse('investment-cancel', kwargs={'pk': self.investment.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que le statut n'a pas changé
        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, Investment.STATUS_CONFIRMED)


class InvestmentPaymentAPITest(TestCase):
    """Tests pour les API de paiements d'investissements."""

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
        
        self.other_investor = User.objects.create_user(
            email='other@venturelink.com',
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

    def test_create_payment(self):
        """Test: un investisseur peut créer un paiement pour son investissement."""
        self.client.force_authenticate(user=self.investor)
        url = reverse('investment-payments-list', kwargs={'investment_pk': self.investment.id})
        
        data = {
            'amount': '15000.00',
            'currency': 'EUR',
            'payment_method': InvestmentPayment.METHOD_BANK_TRANSFER,
            'transaction_id': 'TX987654321',
            'payment_details': {'bank': 'Test Bank', 'reference': 'REF123'}
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que le paiement a été créé
        self.assertTrue(InvestmentPayment.objects.filter(
            investment=self.investment,
            amount=Decimal('15000.00'),
            transaction_id='TX987654321'
        ).exists())

    def test_other_investor_cannot_create_payment(self):
        """Test: un autre investisseur ne peut pas créer de paiement pour un investissement qui n'est pas le sien."""
        self.client.force_authenticate(user=self.other_investor)
        url = reverse('investment-payments-list', kwargs={'investment_pk': self.investment.id})
        
        data = {
            'amount': '15000.00',
            'currency': 'EUR',
            'payment_method': InvestmentPayment.METHOD_BANK_TRANSFER,
            'transaction_id': 'TX987654321'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Vérifier qu'aucun paiement n'a été créé
        self.assertFalse(InvestmentPayment.objects.filter(
            transaction_id='TX987654321'
        ).exists())

    def test_list_payments(self):
        """Test: les parties impliquées peuvent voir les paiements d'un investissement."""
        # Créer un paiement
        payment = InvestmentPayment.objects.create(
            investment=self.investment,
            amount=Decimal('15000.00'),
            currency='EUR',
            payment_method=InvestmentPayment.METHOD_BANK_TRANSFER,
            transaction_id='TX123456',
            status=InvestmentPayment.STATUS_PENDING
        )
        
        url = reverse('investment-payments-list', kwargs={'investment_pk': self.investment.id})
        
        # Investisseur propriétaire
        self.client.force_authenticate(user=self.investor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(payment.id))
        
        # Entrepreneur du projet
        self.client.force_authenticate(user=self.entrepreneur)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Autre investisseur non impliqué
        self.client.force_authenticate(user=self.other_investor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 