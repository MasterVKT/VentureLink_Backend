"""
Tests pour les services de l'application investments.
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.investments.models import (
    Investment, InvestmentPayment, InvestmentHistory,
    Repayment, RepaymentSchedule
)
from apps.investments.services import (
    InvestmentService, RepaymentService, RepaymentScheduleService
)
from apps.core.services import CurrencyService


class InvestmentServiceTest(TestCase):
    """Tests pour le service InvestmentService."""

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

    def test_get_investments_with_filters(self):
        """Test la récupération d'investissements avec filtres."""
        # Créer un autre investissement avec statut différent
        Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('5000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_LOAN,
            interest_rate=Decimal('5.00'),
            term_months=12,
            status=Investment.STATUS_APPROVED
        )
        
        # Tester le filtre par statut
        investments = InvestmentService.get_investments(status=Investment.STATUS_PENDING)
        self.assertEqual(investments.count(), 1)
        self.assertEqual(investments[0].id, self.investment.id)
        
        # Tester le filtre par type d'investissement
        investments = InvestmentService.get_investments(investment_type=Investment.TYPE_LOAN)
        self.assertEqual(investments.count(), 1)
        self.assertEqual(investments[0].investment_type, Investment.TYPE_LOAN)
        
        # Tester le filtre par utilisateur
        investments = InvestmentService.get_investments(user=self.investor)
        self.assertEqual(investments.count(), 2)

    @patch('apps.core.services.CurrencyService.convert_amount')
    def test_get_investment_with_currency_conversion(self, mock_convert_amount):
        """Test la récupération d'un investissement avec conversion de devise."""
        # Configurer le mock pour la conversion
        mock_convert_amount.return_value = Decimal('16500.00')
        
        # Appeler le service avec demande de conversion
        investment_detail = InvestmentService.get_investment_detail(
            investment_id=self.investment.id,
            user=self.investor,
            target_currency='USD'
        )
        
        # Vérifier que le service de conversion a été appelé
        mock_convert_amount.assert_called_once_with(
            amount=self.investment.amount,
            from_currency=self.investment.currency,
            to_currency='USD'
        )
        
        # Vérifier que les données converties sont présentes
        self.assertEqual(investment_detail['amount_converted'], Decimal('16500.00'))
        self.assertEqual(investment_detail['currency_converted'], 'USD')

    def test_create_investment_payment(self):
        """Test la création d'un paiement d'investissement."""
        payment = InvestmentService.create_payment(
            investment_id=self.investment.id,
            user=self.investor,
            amount=Decimal('15000.00'),
            currency='EUR',
            payment_method=InvestmentPayment.METHOD_CREDIT_CARD,
            transaction_id='tx_123456',
            payment_details={'card_last4': '4242'}
        )
        
        # Vérifier que le paiement a été créé correctement
        self.assertEqual(payment.investment, self.investment)
        self.assertEqual(payment.amount, Decimal('15000.00'))
        self.assertEqual(payment.currency, 'EUR')
        self.assertEqual(payment.payment_method, InvestmentPayment.METHOD_CREDIT_CARD)
        self.assertEqual(payment.transaction_id, 'tx_123456')
        self.assertEqual(payment.payment_details, {'card_last4': '4242'})
        self.assertEqual(payment.status, InvestmentPayment.STATUS_PENDING)


class RepaymentServiceTest(TestCase):
    """Tests pour le service RepaymentService."""

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
            full_description='Une description plus longue et détaillée du projet de test.',
            category=self.category,
            is_draft=False  # Projet publié
        )
        
        # Créer un investissement de type prêt
        self.investment = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('12000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_LOAN,
            interest_rate=Decimal('5.00'),
            term_months=12,
            status=Investment.STATUS_APPROVED
        )

    def test_create_repayment(self):
        """Test la création d'un remboursement."""
        repayment = RepaymentService.create_repayment(
            user=self.entrepreneur,
            investment_id=self.investment.id,
            amount=Decimal('1100.00'),
            currency='EUR',
            repayment_type=Repayment.TYPE_MIXED,
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00'),
            payment_method=Repayment.METHOD_BANK_TRANSFER
        )
        
        # Vérifier que le remboursement a été créé correctement
        self.assertEqual(repayment.investment, self.investment)
        self.assertEqual(repayment.paid_by, self.entrepreneur)
        self.assertEqual(repayment.received_by, self.investor)
        self.assertEqual(repayment.amount, Decimal('1100.00'))
        self.assertEqual(repayment.currency, 'EUR')
        self.assertEqual(repayment.repayment_type, Repayment.TYPE_MIXED)
        self.assertEqual(repayment.principal_amount, Decimal('1000.00'))
        self.assertEqual(repayment.interest_amount, Decimal('100.00'))
        self.assertEqual(repayment.status, Repayment.STATUS_PENDING)

    @patch('apps.core.services.CurrencyService.convert_amount')
    def test_get_repayment_with_currency_conversion(self, mock_convert_amount):
        """Test la récupération d'un remboursement avec conversion de devise."""
        # Créer un remboursement
        repayment = RepaymentService.create_repayment(
            user=self.entrepreneur,
            investment_id=self.investment.id,
            amount=Decimal('1100.00'),
            currency='EUR',
            repayment_type=Repayment.TYPE_MIXED,
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00')
        )
        
        # Configurer les mocks pour la conversion
        mock_convert_amount.side_effect = [
            Decimal('1210.00'),  # montant total
            Decimal('1100.00'),  # principal
            Decimal('110.00')    # intérêts
        ]
        
        # Appeler le service avec demande de conversion
        repayment_detail = RepaymentService.get_repayment_detail(
            repayment_id=repayment.id,
            user=self.entrepreneur,
            target_currency='USD'
        )
        
        # Vérifier que le service de conversion a été appelé
        self.assertEqual(mock_convert_amount.call_count, 3)
        
        # Vérifier que les données converties sont présentes
        self.assertEqual(repayment_detail['amount_converted'], Decimal('1210.00'))
        self.assertEqual(repayment_detail['currency_converted'], 'USD')
        self.assertEqual(repayment_detail['principal_amount_converted'], Decimal('1100.00'))
        self.assertEqual(repayment_detail['interest_amount_converted'], Decimal('110.00'))


class RepaymentScheduleServiceTest(TestCase):
    """Tests pour le service RepaymentScheduleService."""

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
            full_description='Une description plus longue et détaillée du projet de test.',
            category=self.category,
            is_draft=False  # Projet publié
        )
        
        # Créer un investissement de type prêt
        self.investment = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('12000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_LOAN,
            interest_rate=Decimal('5.00'),
            term_months=12,
            status=Investment.STATUS_APPROVED
        )

    def test_generate_loan_schedule(self):
        """Test la génération d'un échéancier de remboursement pour un prêt."""
        start_date = timezone.now().date()
        
        # Générer l'échéancier
        schedule_items = RepaymentScheduleService.generate_loan_schedule(
            investment_id=self.investment.id,
            user=self.entrepreneur,
            start_date=start_date,
            payment_frequency_months=1
        )
        
        # Vérifier que l'échéancier a été généré correctement
        self.assertEqual(len(schedule_items), 12)  # 12 mois
        
        # Vérifier le premier paiement
        first_payment = schedule_items[0]
        self.assertEqual(first_payment.investment, self.investment)
        self.assertEqual(first_payment.currency, 'EUR')
        self.assertEqual(first_payment.is_paid, False)
        
        # Vérifier que la somme des montants est correcte
        total_amount = sum(item.amount for item in schedule_items)
        # Le total doit être supérieur au montant de l'investissement (principal + intérêts)
        self.assertGreater(total_amount, self.investment.amount)
        
        # Vérifier que les dates sont espacées d'un mois
        for i in range(1, len(schedule_items)):
            self.assertEqual(
                (schedule_items[i].due_date.month - schedule_items[i-1].due_date.month) % 12,
                1
            )

    def test_link_repayment_to_schedule(self):
        """Test la liaison d'un remboursement à un élément d'échéancier."""
        # Créer un échéancier
        start_date = timezone.now().date()
        schedule_items = RepaymentScheduleService.generate_loan_schedule(
            investment_id=self.investment.id,
            user=self.entrepreneur,
            start_date=start_date
        )
        
        # Créer un remboursement
        repayment = RepaymentService.create_repayment(
            user=self.entrepreneur,
            investment_id=self.investment.id,
            amount=schedule_items[0].amount,
            currency='EUR',
            repayment_type=Repayment.TYPE_MIXED,
            principal_amount=schedule_items[0].principal_amount,
            interest_amount=schedule_items[0].interest_amount
        )
        
        # Lier le remboursement à l'échéancier
        linked_item = RepaymentScheduleService.link_repayment_to_schedule(
            schedule_item_id=schedule_items[0].id,
            repayment_id=repayment.id,
            user=self.entrepreneur
        )
        
        # Vérifier que la liaison a été effectuée
        self.assertEqual(linked_item.repayment, repayment)
        
        # Mettre à jour le statut du remboursement
        repayment.status = Repayment.STATUS_COMPLETED
        repayment.save()
        
        # Vérifier que l'élément d'échéancier est marqué comme payé
        linked_item.refresh_from_db()
        self.assertTrue(linked_item.is_paid) 