"""
Tests des serializers de paiement (Tâche B3.7).

Couvre :
- PaymentSerializer        → lecture d'un paiement
- PaymentCreateSerializer  → validation création paiement
- RefundSerializer         → lecture d'un remboursement
- RefundCreateSerializer   → validation création remboursement
- SubscriptionPlanSerializer → lecture d'un plan
- UserSubscriptionSerializer → lecture d'un abonnement
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.payments.models import Payment, Refund, SubscriptionPlan, UserSubscription
from apps.payments.serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    RefundSerializer,
    RefundCreateSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Tests — PaymentSerializer
# ---------------------------------------------------------------------------

class PaymentSerializerTest(TestCase):
    """Tests du PaymentSerializer (lecture)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            currency='XAF',
            description='Test paiement',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            status=Payment.PaymentStatus.PENDING,
            external_payment_id='MCP-SER-001',
            metadata={},
        )

    def test_serializes_all_required_fields(self):
        """Le serializer doit inclure tous les champs requis."""
        serializer = PaymentSerializer(self.payment)
        data = serializer.data
        required_fields = [
            'id', 'user', 'amount', 'currency', 'status', 'status_display',
            'payment_type', 'payment_type_display', 'external_payment_id',
            'description', 'metadata', 'is_test', 'created_at',
            'is_completed', 'is_refunded', 'can_be_refunded',
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Champ manquant: {field}")

    def test_status_display_is_human_readable(self):
        """status_display doit être lisible par un humain."""
        serializer = PaymentSerializer(self.payment)
        self.assertEqual(serializer.data['status_display'], 'En attente')

    def test_payment_type_display_is_human_readable(self):
        """payment_type_display doit être lisible."""
        serializer = PaymentSerializer(self.payment)
        self.assertEqual(serializer.data['payment_type_display'], 'Abonnement')

    def test_is_completed_false_for_pending(self):
        """is_completed doit être False pour un paiement en attente."""
        serializer = PaymentSerializer(self.payment)
        self.assertFalse(serializer.data['is_completed'])

    def test_is_completed_true_for_completed(self):
        """is_completed doit être True pour un paiement complété."""
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.save()
        serializer = PaymentSerializer(self.payment)
        self.assertTrue(serializer.data['is_completed'])

    def test_can_be_refunded_true_for_completed(self):
        """can_be_refunded doit être True pour un paiement complété."""
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.save()
        serializer = PaymentSerializer(self.payment)
        self.assertTrue(serializer.data['can_be_refunded'])

    def test_refunds_list_included(self):
        """La liste des remboursements doit être incluse."""
        serializer = PaymentSerializer(self.payment)
        self.assertIn('refunds', serializer.data)
        self.assertIsInstance(serializer.data['refunds'], list)


# ---------------------------------------------------------------------------
# Tests — PaymentCreateSerializer
# ---------------------------------------------------------------------------

class PaymentCreateSerializerTest(TestCase):
    """Tests du PaymentCreateSerializer (validation)."""

    def test_valid_data_passes(self):
        """Des données valides doivent passer la validation."""
        data = {
            'amount': '5000.00',
            'currency': 'XAF',
            'description': 'Test paiement',
            'payment_type': Payment.PaymentType.SUBSCRIPTION,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_currency_normalized_to_uppercase(self):
        """La devise doit être normalisée en majuscules."""
        data = {
            'amount': '5000.00',
            'currency': 'xaf',
            'description': 'Test',
            'payment_type': Payment.PaymentType.OTHER,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['currency'], 'XAF')

    def test_amount_zero_fails(self):
        """Un montant de 0 doit échouer la validation."""
        data = {
            'amount': '0.00',
            'currency': 'XAF',
            'description': 'Test',
            'payment_type': Payment.PaymentType.OTHER,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

    def test_negative_amount_fails(self):
        """Un montant négatif doit échouer."""
        data = {
            'amount': '-100.00',
            'currency': 'XAF',
            'description': 'Test',
            'payment_type': Payment.PaymentType.OTHER,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_missing_description_fails(self):
        """Sans description, la validation doit échouer."""
        data = {
            'amount': '5000.00',
            'currency': 'XAF',
            'payment_type': Payment.PaymentType.OTHER,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

    def test_optional_fields_not_required(self):
        """Les champs optionnels ne doivent pas être requis."""
        data = {
            'amount': '5000.00',
            'currency': 'XAF',
            'description': 'Test',
            'payment_type': Payment.PaymentType.OTHER,
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ---------------------------------------------------------------------------
# Tests — RefundCreateSerializer
# ---------------------------------------------------------------------------

class RefundCreateSerializerTest(TestCase):
    """Tests du RefundCreateSerializer (validation)."""

    def test_empty_data_is_valid(self):
        """Tous les champs sont optionnels — données vides valides."""
        serializer = RefundCreateSerializer(data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_partial_refund_with_amount(self):
        """Un remboursement partiel avec montant doit être valide."""
        serializer = RefundCreateSerializer(data={'amount': '2500.00'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['amount'], Decimal('2500.00'))

    def test_with_reason_and_notes(self):
        """Raison et notes doivent être acceptées."""
        serializer = RefundCreateSerializer(data={
            'amount': '5000.00',
            'reason': 'Demande client',
            'notes': 'Note interne',
        })
        self.assertTrue(serializer.is_valid())


# ---------------------------------------------------------------------------
# Tests — SubscriptionPlanSerializer
# ---------------------------------------------------------------------------

class SubscriptionPlanSerializerTest(TestCase):
    """Tests du SubscriptionPlanSerializer."""

    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            id='basic_monthly',
            name='BASIC Mensuel',
            description='Plan de base mensuel',
            price_xaf=Decimal('5000'),
            price_eur=Decimal('7.63'),
            price_usd=Decimal('8.33'),
            duration_days=30,
            max_projects=5,
            max_investments=10,
            max_messages=100,
            features=['analytics', 'support'],
            is_active=True,
            is_popular=False,
            is_free=False,
            trial_days=7,
        )

    def test_serializes_all_required_fields(self):
        """Tous les champs requis doivent être présents."""
        serializer = SubscriptionPlanSerializer(self.plan)
        data = serializer.data
        required_fields = [
            'id', 'name', 'description',
            'price_xaf', 'price_eur', 'price_usd',
            'formatted_price_xaf', 'formatted_price_eur', 'formatted_price_usd',
            'duration_days', 'duration_months',
            'features', 'max_projects', 'max_investments', 'max_messages',
            'is_unlimited_projects', 'is_unlimited_investments', 'is_unlimited_messages',
            'is_active', 'is_popular', 'is_free', 'trial_days',
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Champ manquant: {field}")

    def test_duration_months_calculated(self):
        """duration_months doit être calculé depuis duration_days."""
        serializer = SubscriptionPlanSerializer(self.plan)
        self.assertEqual(serializer.data['duration_months'], 1)

    def test_formatted_prices_include_currency_symbol(self):
        """Les prix formatés doivent inclure le symbole de devise."""
        serializer = SubscriptionPlanSerializer(self.plan)
        data = serializer.data
        self.assertIn('FCFA', data['formatted_price_xaf'])
        self.assertIn('€', data['formatted_price_eur'])
        self.assertIn('$', data['formatted_price_usd'])

    def test_unlimited_flags_false_when_limits_set(self):
        """Les flags illimité doivent être False quand des limites sont définies."""
        serializer = SubscriptionPlanSerializer(self.plan)
        data = serializer.data
        self.assertFalse(data['is_unlimited_projects'])
        self.assertFalse(data['is_unlimited_investments'])
        self.assertFalse(data['is_unlimited_messages'])

    def test_unlimited_flags_true_when_zero(self):
        """Les flags illimité doivent être True quand les limites sont à 0."""
        self.plan.max_projects = 0
        self.plan.max_investments = 0
        self.plan.max_messages = 0
        self.plan.save()
        serializer = SubscriptionPlanSerializer(self.plan)
        data = serializer.data
        self.assertTrue(data['is_unlimited_projects'])
        self.assertTrue(data['is_unlimited_investments'])
        self.assertTrue(data['is_unlimited_messages'])

    def test_features_is_list(self):
        """features doit être une liste."""
        serializer = SubscriptionPlanSerializer(self.plan)
        self.assertIsInstance(serializer.data['features'], list)


# ---------------------------------------------------------------------------
# Tests — UserSubscriptionSerializer
# ---------------------------------------------------------------------------

class UserSubscriptionSerializerTest(TestCase):
    """Tests du UserSubscriptionSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='sub@example.com',
            password='testpass123',
        )
        self.plan = SubscriptionPlan.objects.create(
            id='basic_monthly',
            name='BASIC Mensuel',
            price_xaf=Decimal('5000'),
            price_eur=Decimal('7.63'),
            price_usd=Decimal('8.33'),
            duration_days=30,
            features=[],
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
            billing_currency='XAF',
        )

    def test_serializes_all_required_fields(self):
        """Tous les champs requis doivent être présents."""
        serializer = UserSubscriptionSerializer(self.subscription)
        data = serializer.data
        required_fields = [
            'id', 'user', 'plan', 'status', 'status_display',
            'started_at', 'expires_at', 'auto_renew', 'billing_currency',
            'is_active', 'is_expired', 'days_remaining',
        ]
        for field in required_fields:
            self.assertIn(field, data, f"Champ manquant: {field}")

    def test_status_display_human_readable(self):
        """status_display doit être lisible."""
        serializer = UserSubscriptionSerializer(self.subscription)
        self.assertEqual(serializer.data['status_display'], 'Actif')

    def test_is_active_true_for_active_subscription(self):
        """is_active doit être True pour un abonnement actif non expiré."""
        serializer = UserSubscriptionSerializer(self.subscription)
        self.assertTrue(serializer.data['is_active'])

    def test_days_remaining_positive(self):
        """days_remaining doit être positif pour un abonnement actif."""
        serializer = UserSubscriptionSerializer(self.subscription)
        self.assertGreater(serializer.data['days_remaining'], 0)

    def test_plan_nested_in_response(self):
        """Le plan doit être imbriqué dans la réponse."""
        serializer = UserSubscriptionSerializer(self.subscription)
        plan_data = serializer.data['plan']
        self.assertEqual(plan_data['id'], 'basic_monthly')
        self.assertEqual(plan_data['name'], 'BASIC Mensuel')

    def test_formatted_current_price_includes_currency(self):
        """formatted_current_price doit inclure la devise."""
        serializer = UserSubscriptionSerializer(self.subscription)
        price = serializer.data['formatted_current_price']
        self.assertIn('FCFA', price)

    def test_expired_subscription_is_not_active(self):
        """Un abonnement expiré ne doit pas être actif."""
        self.subscription.expires_at = timezone.now() - timezone.timedelta(days=1)
        self.subscription.save()
        serializer = UserSubscriptionSerializer(self.subscription)
        self.assertFalse(serializer.data['is_active'])
        self.assertTrue(serializer.data['is_expired'])
