"""
Tests pour les modèles de l'application investments.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.investments.models import (
    Investment, InvestmentPayment, 
    RepaymentSchedule, RepaymentTransaction
)


class InvestmentModelTest(TestCase):
    """Tests pour le modèle Investment."""

    def setUp(self):
        # Créer des utilisateurs
        self.entrepreneur = User.objects.create_user(
            email='entrepreneur@venturelink.com',
            password='testpassword',
            first_name='Entrepreneur',
            last_name='Test',
            user_type='ENTREPRENEUR'
        )
        
        self.investor = User.objects.create_user(
            email='investor@venturelink.com',
            password='testpassword',
            first_name='Investor',
            last_name='Test',
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
            stage=Project.STAGE_PROTOTYPE,
            funding_min=Decimal('10000.00'),
            funding_max=Decimal('50000.00'),
            funding_currency='EUR',
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

    def test_investment_creation(self):
        """Test la création d'un investissement."""
        self.assertEqual(self.investment.project, self.project)
        self.assertEqual(self.investment.investor, self.investor)
        self.assertEqual(self.investment.amount, Decimal('15000.00'))
        self.assertEqual(self.investment.currency, 'EUR')
        self.assertEqual(self.investment.investment_type, Investment.TYPE_EQUITY)
        self.assertEqual(self.investment.equity_percentage, Decimal('5.00'))
        self.assertEqual(self.investment.status, Investment.STATUS_PENDING)
        self.assertIsNone(self.investment.confirmed_at)
        self.assertEqual(str(self.investment), f'Investissement de 15000.00 EUR par {self.investor.email}')

    def test_investment_confirmation(self):
        """Test la confirmation d'un investissement."""
        self.investment.status = Investment.STATUS_CONFIRMED
        self.investment.confirmed_at = timezone.now()
        self.investment.save()
        
        self.assertEqual(self.investment.status, Investment.STATUS_CONFIRMED)
        self.assertIsNotNone(self.investment.confirmed_at)


class InvestmentPaymentModelTest(TestCase):
    """Tests pour le modèle InvestmentPayment."""

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

    def test_payment_creation(self):
        """Test la création d'un paiement d'investissement."""
        self.assertEqual(self.payment.investment, self.investment)
        self.assertEqual(self.payment.amount, Decimal('15000.00'))
        self.assertEqual(self.payment.currency, 'EUR')
        self.assertEqual(self.payment.payment_method, InvestmentPayment.METHOD_BANK_TRANSFER)
        self.assertEqual(self.payment.transaction_id, 'TX123456789')
        self.assertEqual(self.payment.status, InvestmentPayment.STATUS_PENDING)
        self.assertIsNone(self.payment.processed_at)

    def test_payment_processing(self):
        """Test le traitement d'un paiement."""
        self.payment.status = InvestmentPayment.STATUS_COMPLETED
        self.payment.processed_at = timezone.now()
        self.payment.save()
        
        self.assertEqual(self.payment.status, InvestmentPayment.STATUS_COMPLETED)
        self.assertIsNotNone(self.payment.processed_at)


class RepaymentScheduleModelTest(TestCase):
    """Tests pour le modèle RepaymentSchedule."""

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
        
        # Créer un investissement
        self.investment = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('15000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_LOAN,
            loan_interest_rate=Decimal('5.00'),
            loan_term_months=24,
            status=Investment.STATUS_CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Créer un échéancier de remboursement
        self.schedule = RepaymentSchedule.objects.create(
            investment=self.investment,
            total_amount=Decimal('16500.00'),  # Principal + intérêts
            currency='EUR',
            payment_frequency=RepaymentSchedule.FREQUENCY_MONTHLY,
            next_payment_date=timezone.now().date() + timedelta(days=30),
            remaining_payments=24
        )

    def test_schedule_creation(self):
        """Test la création d'un échéancier de remboursement."""
        self.assertEqual(self.schedule.investment, self.investment)
        self.assertEqual(self.schedule.total_amount, Decimal('16500.00'))
        self.assertEqual(self.schedule.currency, 'EUR')
        self.assertEqual(self.schedule.payment_frequency, RepaymentSchedule.FREQUENCY_MONTHLY)
        self.assertEqual(self.schedule.remaining_payments, 24)
        
        # Calculer le montant par versement
        expected_installment = Decimal('16500.00') / 24
        self.assertEqual(self.schedule.installment_amount, expected_installment)


class RepaymentTransactionModelTest(TestCase):
    """Tests pour le modèle RepaymentTransaction."""

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
        
        # Créer un investissement
        self.investment = Investment.objects.create(
            project=self.project,
            investor=self.investor,
            amount=Decimal('15000.00'),
            currency='EUR',
            investment_type=Investment.TYPE_LOAN,
            loan_interest_rate=Decimal('5.00'),
            loan_term_months=24,
            status=Investment.STATUS_CONFIRMED,
            confirmed_at=timezone.now()
        )
        
        # Créer un échéancier de remboursement
        self.schedule = RepaymentSchedule.objects.create(
            investment=self.investment,
            total_amount=Decimal('16500.00'),  # Principal + intérêts
            currency='EUR',
            payment_frequency=RepaymentSchedule.FREQUENCY_MONTHLY,
            next_payment_date=timezone.now().date() + timedelta(days=30),
            remaining_payments=24
        )
        
        # Créer une transaction de remboursement
        self.transaction = RepaymentTransaction.objects.create(
            schedule=self.schedule,
            amount=Decimal('687.50'),  # Montant d'un versement mensuel
            currency='EUR',
            payment_method=RepaymentTransaction.METHOD_BANK_TRANSFER,
            transaction_id='RPY123456789',
            status=RepaymentTransaction.STATUS_COMPLETED,
            payment_date=timezone.now().date()
        )

    def test_transaction_creation(self):
        """Test la création d'une transaction de remboursement."""
        self.assertEqual(self.transaction.schedule, self.schedule)
        self.assertEqual(self.transaction.amount, Decimal('687.50'))
        self.assertEqual(self.transaction.currency, 'EUR')
        self.assertEqual(self.transaction.payment_method, RepaymentTransaction.METHOD_BANK_TRANSFER)
        self.assertEqual(self.transaction.transaction_id, 'RPY123456789')
        self.assertEqual(self.transaction.status, RepaymentTransaction.STATUS_COMPLETED)
        self.assertIsNotNone(self.transaction.payment_date)

    def test_transaction_update_schedule(self):
        """Test la mise à jour de l'échéancier après un paiement."""
        # Avant le paiement
        original_remaining = self.schedule.remaining_payments
        
        # Simuler la mise à jour de l'échéancier après paiement
        self.schedule.remaining_payments -= 1
        next_date = self.schedule.next_payment_date + timedelta(days=30)
        self.schedule.next_payment_date = next_date
        self.schedule.save()
        
        # Vérifier les changements
        self.assertEqual(self.schedule.remaining_payments, original_remaining - 1)
        self.assertEqual(self.schedule.next_payment_date, next_date) 