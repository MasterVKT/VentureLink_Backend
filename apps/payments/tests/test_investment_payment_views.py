"""
Tests de l'endpoint B3.2 — Initiation paiement investissement.

POST /api/v1/payments/initiate/

Couvre :
- Initiation réussie → 201 + payment_url
- Validation investment_id (inexistant, mauvais propriétaire, déjà payé, annulé)
- Validation phone_number (vide, trop court, normalisation +237)
- Authentification requise (401 sans token)
- Erreur My-CoolPay → 402
- Vérification Payment créé en base avec bon type et statut
- Vérification Investment passe au statut APPROVED
- Vérification lien GenericForeignKey Payment → Investment
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status

from apps.payments.models import Payment
from apps.payments.serializers.investment_payment_serializers import (
    InitiateInvestmentPaymentSerializer,
)
from apps.investments.models import Investment
from apps.projects.models import Project, ProjectCategory

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(email='investor@test.com', password='testpass123'):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Alice',
        last_name='Martin',
    )


def create_category():
    return ProjectCategory.objects.create(
        name_fr='Technologie',
        name_en='Technology',
    )


def create_project(creator, title='Mon Super Projet de Tech'):
    cat = create_category()
    return Project.objects.create(
        creator=creator,
        title=title,
        short_description='Description courte du projet de test pour VentureLink',
        full_description='Description complète du projet de test. ' * 5,
        category=cat,
        stage=Project.STAGE_IDEA,
    )


def create_investment(investor, project, amount=Decimal('50000.00'),
                      currency='XAF', inv_status=Investment.STATUS_PENDING):
    return Investment.objects.create(
        investor=investor,
        project=project,
        amount=amount,
        currency=currency,
        investment_type=Investment.TYPE_EQUITY,
        status=inv_status,
    )


# ---------------------------------------------------------------------------
# Tests — Endpoint POST /api/v1/payments/initiate/
# ---------------------------------------------------------------------------

class InitiateInvestmentPaymentViewTest(TestCase):
    """Tests de l'endpoint POST /api/v1/payments/initiate/"""

    URL = '/api/v1/payments/initiate/'

    def setUp(self):
        self.client = APIClient()
        self.investor = create_user('investor@test.com')
        self.other_user = create_user('other@test.com')
        self.project_owner = create_user('owner@test.com')
        self.project = create_project(self.project_owner)
        self.investment = create_investment(self.investor, self.project)
        self.client.force_authenticate(user=self.investor)

    # ------------------------------------------------------------------
    # Cas nominal
    # ------------------------------------------------------------------

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_initiate_payment_success_returns_201(self, mock_paylink):
        """Une requête valide doit retourner 201 avec payment_url."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/INV123',
            'transaction_ref': 'MCP-INV-123',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
            'currency': 'XAF',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment_url', response.data)
        self.assertIn('payment_id', response.data)
        self.assertIn('transaction_ref', response.data)
        self.assertIn('investment_id', response.data)
        self.assertIn('amount', response.data)
        self.assertIn('currency', response.data)
        self.assertIn('status', response.data)
        self.assertIn('expires_at', response.data)
        self.assertIn('message', response.data)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_payment_created_in_database(self, mock_paylink):
        """Un Payment doit être créé en base avec le bon type et statut."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/INV456',
            'transaction_ref': 'MCP-INV-456',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.data['payment_id'])
        self.assertEqual(payment.user, self.investor)
        self.assertEqual(payment.payment_type, Payment.PaymentType.INVESTMENT)
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(payment.currency, 'XAF')
        self.assertEqual(payment.external_payment_id, 'MCP-INV-456')
        self.assertEqual(payment.external_checkout_url,
                         'https://pay.my-coolpay.com/pay/INV456')

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_payment_linked_to_investment_via_generic_fk(self, mock_paylink):
        """Le Payment doit être lié à l'Investment via GenericForeignKey."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/INV789',
            'transaction_ref': 'MCP-INV-789',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.data['payment_id'])
        ct = ContentType.objects.get_for_model(Investment)
        self.assertEqual(payment.content_type, ct)
        self.assertEqual(payment.object_id, self.investment.id)
        self.assertEqual(payment.related_object, self.investment)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_investment_status_becomes_approved(self, mock_paylink):
        """L'investissement doit passer au statut APPROVED après initiation."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/INV999',
            'transaction_ref': 'MCP-INV-999',
        }

        self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, Investment.STATUS_APPROVED)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_payment_metadata_contains_investment_info(self, mock_paylink):
        """Les métadonnées du Payment doivent contenir les infos de l'investissement."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/META',
            'transaction_ref': 'MCP-META',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        payment = Payment.objects.get(id=response.data['payment_id'])
        self.assertIn('investment_id', payment.metadata)
        self.assertIn('project_id', payment.metadata)
        self.assertIn('project_title', payment.metadata)
        self.assertIn('reference', payment.metadata)
        self.assertEqual(payment.metadata['investment_id'], str(self.investment.id))

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_payment_url_in_response_matches_mycoolpay(self, mock_paylink):
        """La payment_url retournée doit correspondre à celle de My-CoolPay."""
        expected_url = 'https://pay.my-coolpay.com/pay/EXACT'
        mock_paylink.return_value = {
            'payment_url': expected_url,
            'transaction_ref': 'MCP-EXACT',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(response.data['payment_url'], expected_url)
        self.assertEqual(response.data['transaction_ref'], 'MCP-EXACT')

    # ------------------------------------------------------------------
    # Validation — investment_id
    # ------------------------------------------------------------------

    def test_missing_investment_id_returns_400(self):
        """Sans investment_id, retourner 400."""
        response = self.client.post(self.URL, {
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_nonexistent_investment_returns_400(self):
        """Un investment_id inexistant doit retourner 400."""
        import uuid
        response = self.client.post(self.URL, {
            'investment_id': str(uuid.uuid4()),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_investment_returns_400(self):
        """Un investissement appartenant à un autre utilisateur doit retourner 400."""
        other_investment = create_investment(self.other_user, self.project)
        response = self.client.post(self.URL, {
            'investment_id': str(other_investment.id),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completed_investment_returns_400(self):
        """Un investissement déjà payé (COMPLETED) doit retourner 400."""
        completed = create_investment(
            self.investor, self.project,
            inv_status=Investment.STATUS_COMPLETED,
        )
        response = self.client.post(self.URL, {
            'investment_id': str(completed.id),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_cancelled_investment_returns_400(self):
        """Un investissement annulé doit retourner 400."""
        cancelled = create_investment(
            self.investor, self.project,
            inv_status=Investment.STATUS_CANCELLED,
        )
        response = self.client.post(self.URL, {
            'investment_id': str(cancelled.id),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejected_investment_returns_400(self):
        """Un investissement rejeté doit retourner 400."""
        rejected = create_investment(
            self.investor, self.project,
            inv_status=Investment.STATUS_REJECTED,
        )
        response = self.client.post(self.URL, {
            'investment_id': str(rejected.id),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Validation — phone_number
    # ------------------------------------------------------------------

    def test_missing_phone_number_returns_400(self):
        """Sans phone_number, retourner 400."""
        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_phone_number_returns_400(self):
        """Un numéro trop court doit retourner 400."""
        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_phone_without_prefix_normalized(self, mock_paylink):
        """Un numéro sans + doit être normalisé avec +237."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/NORM',
            'transaction_ref': 'MCP-NORM',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '690000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que le numéro normalisé est dans les métadonnées
        payment = Payment.objects.get(id=response.data['payment_id'])
        self.assertTrue(payment.metadata['phone_number'].startswith('+237'))

    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------

    def test_unauthenticated_returns_401(self):
        """Sans authentification, retourner 401."""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # Erreur My-CoolPay
    # ------------------------------------------------------------------

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_mycoolpay_error_returns_402(self, mock_paylink):
        """Une erreur My-CoolPay doit retourner 402."""
        from apps.payments.services.mycoolpay_service import MyCoolPayError
        mock_paylink.side_effect = MyCoolPayError("Erreur API My-CoolPay: HTTP 500")

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('error', response.data)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_mycoolpay_error_does_not_create_payment(self, mock_paylink):
        """En cas d'erreur My-CoolPay, aucun Payment ne doit être créé."""
        from apps.payments.services.mycoolpay_service import MyCoolPayError
        mock_paylink.side_effect = MyCoolPayError("Timeout")

        initial_count = Payment.objects.count()

        self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(Payment.objects.count(), initial_count)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_mycoolpay_error_does_not_change_investment_status(self, mock_paylink):
        """En cas d'erreur My-CoolPay, le statut de l'investissement ne doit pas changer."""
        from apps.payments.services.mycoolpay_service import MyCoolPayError
        mock_paylink.side_effect = MyCoolPayError("Timeout")

        original_status = self.investment.status

        self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        }, format='json')

        self.investment.refresh_from_db()
        self.assertEqual(self.investment.status, original_status)

    # ------------------------------------------------------------------
    # Devise
    # ------------------------------------------------------------------

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_default_currency_is_xaf(self, mock_paylink):
        """La devise par défaut doit être XAF."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/CUR',
            'transaction_ref': 'MCP-CUR',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
            # Pas de currency → XAF par défaut
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'XAF')

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_eur_currency_accepted(self, mock_paylink):
        """La devise EUR doit être acceptée."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/EUR',
            'transaction_ref': 'MCP-EUR',
        }

        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
            'currency': 'EUR',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['currency'], 'EUR')

    def test_invalid_currency_returns_400(self):
        """Une devise non supportée doit retourner 400."""
        response = self.client.post(self.URL, {
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
            'currency': 'GBP',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Tests — Serializer InitiateInvestmentPaymentSerializer
# ---------------------------------------------------------------------------

class InitiateInvestmentPaymentSerializerTest(TestCase):
    """Tests unitaires du serializer de validation B3.2."""

    def setUp(self):
        self.investor = create_user('ser_investor@test.com')
        self.project_owner = create_user('ser_owner@test.com')
        self.project = create_project(self.project_owner, 'Projet Serializer Test')
        self.investment = create_investment(self.investor, self.project)

        # Simuler un request avec l'utilisateur
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        self.request = factory.post('/')
        self.request.user = self.investor

    def _get_serializer(self, data):
        return InitiateInvestmentPaymentSerializer(
            data=data,
            context={'request': self.request},
        )

    def test_valid_data_passes(self):
        """Des données valides doivent passer la validation."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_phone_normalized_without_prefix(self):
        """Un numéro sans + doit être normalisé avec +237."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '690000000',
        })
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.validated_data['phone_number'].startswith('+237'))

    def test_phone_with_spaces_accepted(self):
        """Un numéro avec espaces doit être accepté."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '+237 690 000 000',
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_empty_phone_fails(self):
        """Un numéro vide doit échouer."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('phone_number', s.errors)

    def test_short_phone_fails(self):
        """Un numéro trop court doit échouer."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '+23712',
        })
        self.assertFalse(s.is_valid())

    def test_completed_investment_fails(self):
        """Un investissement COMPLETED doit échouer."""
        completed = create_investment(
            self.investor, self.project,
            inv_status=Investment.STATUS_COMPLETED,
        )
        s = self._get_serializer({
            'investment_id': str(completed.id),
            'phone_number': '+237690000000',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('investment_id', s.errors)

    def test_get_investment_returns_object(self):
        """get_investment() doit retourner l'objet Investment après validation."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        })
        s.is_valid()
        inv = s.get_investment()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.id, self.investment.id)

    def test_default_currency_is_xaf(self):
        """La devise par défaut doit être XAF."""
        s = self._get_serializer({
            'investment_id': str(self.investment.id),
            'phone_number': '+237690000000',
        })
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data.get('currency', 'XAF'), 'XAF')
