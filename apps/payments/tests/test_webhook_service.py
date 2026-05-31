"""
Tests pour le service de webhook My-CoolPay (Tâche B3.3).

Couvre :
- Vérification de signature HMAC
- Routage des événements
- Traitement payment.success (avec mise à jour investissement)
- Traitement payment.failed
- Traitement payment.refunded
- Traitement subscription.renewed
- Traitement subscription.cancelled
- Endpoint webhook HTTP (vérification signature + réponse 200)
"""
import json
import hmac
import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.payments.models import Payment, Refund, UserSubscription, SubscriptionPlan
from apps.payments.services.webhook_service import WebhookService

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signature(secret: str, payload: str) -> str:
    """Générer une signature HMAC-SHA256 valide."""
    return hmac.new(
        key=secret.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Tests de vérification de signature
# ---------------------------------------------------------------------------

class WebhookSignatureTest(TestCase):
    """Tests de vérification de signature HMAC."""

    SECRET = 'test-webhook-secret-b3'

    def test_valid_signature_accepted(self):
        """Une signature HMAC valide doit être acceptée."""
        payload = json.dumps({'event_type': 'payment.success', 'transaction_ref': 'MCP-001'})
        signature = _make_signature(self.SECRET, payload)

        self.assertTrue(WebhookService.verify_signature(payload, signature, self.SECRET))

    def test_invalid_signature_rejected(self):
        """Une signature incorrecte doit être rejetée."""
        payload = json.dumps({'event_type': 'payment.success'})
        self.assertFalse(
            WebhookService.verify_signature(payload, 'bad-signature', self.SECRET)
        )

    def test_tampered_payload_rejected(self):
        """Un payload modifié après signature doit être rejeté."""
        original = json.dumps({'amount': 5000})
        signature = _make_signature(self.SECRET, original)

        tampered = json.dumps({'amount': 1})
        self.assertFalse(WebhookService.verify_signature(tampered, signature, self.SECRET))

    def test_empty_inputs_rejected(self):
        """Les entrées vides doivent être rejetées."""
        payload = json.dumps({'test': 1})
        sig = _make_signature(self.SECRET, payload)

        self.assertFalse(WebhookService.verify_signature('', sig, self.SECRET))
        self.assertFalse(WebhookService.verify_signature(payload, '', self.SECRET))
        self.assertFalse(WebhookService.verify_signature(payload, sig, ''))

    def test_signature_case_insensitive(self):
        """La comparaison doit être insensible à la casse."""
        payload = json.dumps({'event_type': 'payment.success'})
        signature = _make_signature(self.SECRET, payload)

        self.assertTrue(
            WebhookService.verify_signature(payload, signature.upper(), self.SECRET)
        )


# ---------------------------------------------------------------------------
# Tests de routage des événements
# ---------------------------------------------------------------------------

class WebhookEventRoutingTest(TestCase):
    """Tests de routage des événements webhook."""

    def test_unknown_event_returns_false(self):
        """Un type d'événement inconnu doit retourner False."""
        result = WebhookService.process_webhook_event({'event_type': 'unknown.event'})
        self.assertFalse(result)

    def test_missing_event_type_returns_false(self):
        """Un événement sans 'event_type' doit retourner False."""
        result = WebhookService.process_webhook_event({'data': 'no_type'})
        self.assertFalse(result)

    def test_payment_success_routed_correctly(self):
        """payment.success doit être routé vers _handle_payment_success."""
        event = {'event_type': 'payment.success', 'transaction_ref': 'MCP-001'}
        with patch.object(WebhookService, '_handle_payment_success', return_value=True) as mock:
            result = WebhookService.process_webhook_event(event)
            self.assertTrue(result)
            mock.assert_called_once_with(event)

    def test_payment_failed_routed_correctly(self):
        """payment.failed doit être routé vers _handle_payment_failed."""
        event = {'event_type': 'payment.failed', 'transaction_ref': 'MCP-001'}
        with patch.object(WebhookService, '_handle_payment_failed', return_value=True) as mock:
            result = WebhookService.process_webhook_event(event)
            self.assertTrue(result)
            mock.assert_called_once_with(event)

    def test_payment_refunded_routed_correctly(self):
        """payment.refunded doit être routé vers _handle_payment_refunded."""
        event = {
            'event_type': 'payment.refunded',
            'transaction_ref': 'MCP-001',
            'refund_ref': 'REF-001',
        }
        with patch.object(WebhookService, '_handle_payment_refunded', return_value=True) as mock:
            result = WebhookService.process_webhook_event(event)
            self.assertTrue(result)
            mock.assert_called_once_with(event)


# ---------------------------------------------------------------------------
# Tests de traitement payment.success
# ---------------------------------------------------------------------------

class WebhookPaymentSuccessTest(TestCase):
    """Tests du handler payment.success."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='investor@example.com',
            password='testpass123',
            first_name='Alice',
            last_name='Martin',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            currency='XAF',
            description='Test paiement',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            external_payment_id='MCP-SUCCESS-001',
            status=Payment.PaymentStatus.PENDING,
            metadata={},
        )

    def test_payment_status_updated_to_completed(self):
        """Le statut du paiement doit passer à COMPLETED."""
        event = {
            'event_type': 'payment.success',
            'transaction_ref': 'MCP-SUCCESS-001',
            'app_transaction_ref': str(self.payment.id),
            'payment_method': 'CM_MOMO',
            'transaction_date': '2026-05-30T10:00:00Z',
        }

        with patch.object(WebhookService, '_notify_payment_success'):
            result = WebhookService._handle_payment_success(event)

        self.assertTrue(result)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.PaymentStatus.COMPLETED)
        self.assertIsNotNone(self.payment.completed_at)

    def test_metadata_enriched_with_webhook_data(self):
        """Les métadonnées du paiement doivent être enrichies avec les données webhook."""
        event = {
            'event_type': 'payment.success',
            'transaction_ref': 'MCP-SUCCESS-001',
            'payment_method': 'CM_OM',
            'transaction_date': '2026-05-30T10:00:00Z',
        }

        with patch.object(WebhookService, '_notify_payment_success'):
            WebhookService._handle_payment_success(event)

        self.payment.refresh_from_db()
        self.assertIn('webhook_transaction_ref', self.payment.metadata)
        self.assertEqual(self.payment.metadata['webhook_payment_method'], 'CM_OM')

    def test_idempotent_already_completed(self):
        """Un paiement déjà complété ne doit pas être retraité."""
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.completed_at = timezone.now()
        self.payment.save()

        event = {
            'event_type': 'payment.success',
            'transaction_ref': 'MCP-SUCCESS-001',
        }

        result = WebhookService._handle_payment_success(event)
        self.assertTrue(result)  # Doit retourner True sans erreur

    def test_unknown_transaction_ref_returns_false(self):
        """Une référence inconnue doit retourner False."""
        event = {
            'event_type': 'payment.success',
            'transaction_ref': 'MCP-UNKNOWN-999',
        }
        result = WebhookService._handle_payment_success(event)
        self.assertFalse(result)

    def test_missing_transaction_ref_returns_false(self):
        """Un événement sans transaction_ref doit retourner False."""
        event = {'event_type': 'payment.success'}
        result = WebhookService._handle_payment_success(event)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Tests de traitement payment.failed
# ---------------------------------------------------------------------------

class WebhookPaymentFailedTest(TestCase):
    """Tests du handler payment.failed."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            currency='XAF',
            description='Test paiement',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            external_payment_id='MCP-FAIL-001',
            status=Payment.PaymentStatus.PENDING,
            metadata={},
        )

    def test_payment_status_updated_to_failed(self):
        """Le statut du paiement doit passer à FAILED."""
        event = {
            'event_type': 'payment.failed',
            'transaction_ref': 'MCP-FAIL-001',
            'error_code': 'insufficient_funds',
            'error_details': 'Solde insuffisant',
            'transaction_date': '2026-05-30T10:00:00Z',
        }

        with patch.object(WebhookService, '_notify_payment_failed'):
            result = WebhookService._handle_payment_failed(event)

        self.assertTrue(result)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.PaymentStatus.FAILED)
        self.assertEqual(self.payment.metadata['webhook_error_code'], 'insufficient_funds')

    def test_idempotent_already_failed(self):
        """Un paiement déjà en échec ne doit pas être retraité."""
        self.payment.status = Payment.PaymentStatus.FAILED
        self.payment.save()

        event = {
            'event_type': 'payment.failed',
            'transaction_ref': 'MCP-FAIL-001',
        }
        result = WebhookService._handle_payment_failed(event)
        self.assertTrue(result)


# ---------------------------------------------------------------------------
# Tests de traitement payment.refunded
# ---------------------------------------------------------------------------

class WebhookPaymentRefundedTest(TestCase):
    """Tests du handler payment.refunded."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            currency='XAF',
            description='Test paiement',
            payment_type=Payment.PaymentType.SUBSCRIPTION,
            external_payment_id='MCP-REFUND-001',
            status=Payment.PaymentStatus.COMPLETED,
            metadata={},
        )

    def test_refund_created_and_payment_updated(self):
        """Un remboursement doit être créé et le paiement mis à jour."""
        event = {
            'event_type': 'payment.refunded',
            'transaction_ref': 'MCP-REFUND-001',
            'refund_ref': 'REF-001',
            'refund_amount': 5000.00,
            'refund_reason': 'Demande client',
        }

        with patch.object(WebhookService, '_notify_refund'):
            result = WebhookService._handle_payment_refunded(event)

        self.assertTrue(result)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.PaymentStatus.REFUNDED)

        refund = Refund.objects.filter(payment=self.payment).first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.status, Refund.RefundStatus.COMPLETED)
        self.assertEqual(float(refund.amount), 5000.00)
        self.assertEqual(refund.external_refund_id, 'REF-001')

    def test_partial_refund_sets_partially_refunded_status(self):
        """Un remboursement partiel doit mettre le statut à PARTIALLY_REFUNDED."""
        event = {
            'event_type': 'payment.refunded',
            'transaction_ref': 'MCP-REFUND-001',
            'refund_ref': 'REF-PARTIAL-001',
            'refund_amount': 2500.00,  # Moitié du montant
        }

        with patch.object(WebhookService, '_notify_refund'):
            result = WebhookService._handle_payment_refunded(event)

        self.assertTrue(result)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.PaymentStatus.PARTIALLY_REFUNDED)

    def test_duplicate_refund_ref_updates_existing(self):
        """Un refund_ref déjà existant doit mettre à jour le remboursement existant."""
        # Créer un remboursement existant
        existing_refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('5000.00'),
            currency='XAF',
            status=Refund.RefundStatus.PENDING,
            external_refund_id='REF-DUP-001',
        )

        event = {
            'event_type': 'payment.refunded',
            'transaction_ref': 'MCP-REFUND-001',
            'refund_ref': 'REF-DUP-001',
            'refund_amount': 5000.00,
        }

        result = WebhookService._handle_payment_refunded(event)
        self.assertTrue(result)

        existing_refund.refresh_from_db()
        self.assertEqual(existing_refund.status, Refund.RefundStatus.COMPLETED)

        # Vérifier qu'aucun doublon n'a été créé
        self.assertEqual(
            Refund.objects.filter(external_refund_id='REF-DUP-001').count(), 1
        )

    def test_missing_refs_returns_false(self):
        """Un événement sans transaction_ref ou refund_ref doit retourner False."""
        event = {'event_type': 'payment.refunded', 'transaction_ref': 'MCP-REFUND-001'}
        result = WebhookService._handle_payment_refunded(event)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Tests de traitement subscription.renewed
# ---------------------------------------------------------------------------

class WebhookSubscriptionRenewedTest(TestCase):
    """Tests du handler subscription.renewed."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='subscriber@example.com',
            password='testpass123',
        )
        self.plan = SubscriptionPlan.objects.create(
            id='basic_monthly',
            name='BASIC Mensuel',
            price_xaf=Decimal('5000'),
            price_eur=Decimal('7.63'),
            price_usd=Decimal('8.33'),
            duration_days=30,
            max_projects=5,
            features=[],
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
            mycoolpay_subscription_id='MCP-SUB-001',
        )

    def test_subscription_period_extended(self):
        """La période de l'abonnement doit être prolongée."""
        original_end = self.subscription.expires_at

        event = {
            'event_type': 'subscription.renewed',
            'subscription_id': 'MCP-SUB-001',
        }

        with patch(
            'apps.notifications.services.notification_service.NotificationService.create_from_template'
        ):
            result = WebhookService._handle_subscription_renewed(event)

        self.assertTrue(result)
        self.subscription.refresh_from_db()
        self.assertGreater(self.subscription.expires_at, original_end)
        self.assertEqual(self.subscription.status, UserSubscription.SubscriptionStatus.ACTIVE)


# ---------------------------------------------------------------------------
# Tests de l'endpoint HTTP webhook
# ---------------------------------------------------------------------------

class WebhookEndpointTest(TestCase):
    """Tests de l'endpoint HTTP POST /api/v1/payments/mycoolpay/webhook/."""

    WEBHOOK_SECRET = 'test-webhook-secret-endpoint'

    def setUp(self):
        self.client = Client()

    def _post_webhook(self, payload: dict, secret: str = None) -> 'HttpResponse':
        """Envoyer un webhook avec signature valide."""
        body = json.dumps(payload)
        sig = _make_signature(secret or self.WEBHOOK_SECRET, body)
        return self.client.post(
            '/api/v1/payments/mycoolpay/webhook/',
            data=body,
            content_type='application/json',
            HTTP_X_MYCOOLPAY_SIGNATURE=sig,
        )

    @patch('apps.payments.services.webhook_service.WebhookService.process_webhook_event', return_value=True)
    def test_valid_webhook_returns_200(self, mock_process):
        """Un webhook avec signature valide doit retourner HTTP 200."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=self.WEBHOOK_SECRET,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self._post_webhook({
                'event_type': 'payment.success',
                'transaction_ref': 'MCP-001',
            })

        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once()

    def test_missing_signature_returns_403(self):
        """Un webhook sans signature doit retourner HTTP 403."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=self.WEBHOOK_SECRET,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=json.dumps({'event_type': 'payment.success'}),
                content_type='application/json',
                # Pas de header X-MyCoolPay-Signature
            )

        self.assertEqual(response.status_code, 403)

    def test_invalid_signature_returns_403(self):
        """Un webhook avec signature invalide doit retourner HTTP 403."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=self.WEBHOOK_SECRET,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=json.dumps({'event_type': 'payment.success'}),
                content_type='application/json',
                HTTP_X_MYCOOLPAY_SIGNATURE='invalid-signature',
            )

        self.assertEqual(response.status_code, 403)

    @patch('apps.payments.services.webhook_service.WebhookService.process_webhook_event', return_value=False)
    def test_processing_error_still_returns_200(self, mock_process):
        """Même si le traitement échoue, le webhook doit retourner 200 (éviter les retentatives)."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=self.WEBHOOK_SECRET,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self._post_webhook({
                'event_type': 'payment.failed',
                'transaction_ref': 'MCP-UNKNOWN',
            })

        self.assertEqual(response.status_code, 200)

    def test_invalid_json_returns_400(self):
        """Un corps JSON invalide doit retourner HTTP 400."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=self.WEBHOOK_SECRET,
            PAYMENT_SANDBOX_MODE=True,
        ):
            body = 'not-valid-json'
            sig = _make_signature(self.WEBHOOK_SECRET, body)
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=body,
                content_type='application/json',
                HTTP_X_MYCOOLPAY_SIGNATURE=sig,
            )

        self.assertEqual(response.status_code, 400)
