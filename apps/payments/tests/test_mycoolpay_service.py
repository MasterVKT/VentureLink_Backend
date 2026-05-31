"""
Tests pour le service My-CoolPay (Tâche B3.1).

Couvre :
- Initialisation du service (sandbox / production)
- Vérification de signature HMAC webhook
- Vérification de signature callback
- Vérification d'IP
- Création de paylink (mock HTTP)
- Initiation payin (mock HTTP)
- Vérification de statut de transaction (mock HTTP)
- Paiement d'abonnement complet (mock HTTP)
"""
import hmac
import hashlib
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from apps.payments.models import Payment, SubscriptionPlan, UserSubscription
from apps.payments.services.mycoolpay_service import MyCoolPayService, MyCoolPayError, get_mycoolpay_service

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hmac(secret: str, message: str) -> str:
    """Générer une signature HMAC-SHA256."""
    return hmac.new(
        key=secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).hexdigest()


def _make_hmac_bytes(secret: str, payload: bytes) -> str:
    """Générer une signature HMAC-SHA256 sur des bytes."""
    return hmac.new(
        key=secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Tests d'initialisation
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='sandbox-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='sandbox-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='sandbox-webhook-secret',
    MYCOOLPAY_PUBLIC_KEY='prod-pub-key',
    MYCOOLPAY_PRIVATE_KEY='prod-priv-key',
    MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET='prod-webhook-secret',
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=True,
)
class MyCoolPayServiceInitTest(TestCase):
    """Tests d'initialisation du service."""

    def test_sandbox_mode_uses_sandbox_keys(self):
        """Le mode sandbox doit utiliser les clés sandbox."""
        service = MyCoolPayService(sandbox=True)
        self.assertTrue(service.sandbox)
        self.assertEqual(service.public_key, 'sandbox-pub-key')
        self.assertEqual(service.private_key, 'sandbox-priv-key')
        self.assertEqual(service.webhook_secret, 'sandbox-webhook-secret')

    def test_production_mode_uses_production_keys(self):
        """Le mode production doit utiliser les clés de production."""
        service = MyCoolPayService(sandbox=False)
        self.assertFalse(service.sandbox)
        self.assertEqual(service.public_key, 'prod-pub-key')
        self.assertEqual(service.private_key, 'prod-priv-key')
        self.assertEqual(service.webhook_secret, 'prod-webhook-secret')

    def test_missing_public_key_raises_error(self):
        """Une clé publique manquante doit lever MyCoolPayError."""
        with self.settings(MYCOOLPAY_SANDBOX_PUBLIC_KEY=''):
            with self.assertRaises(MyCoolPayError):
                MyCoolPayService(sandbox=True)

    def test_get_mycoolpay_service_returns_sandbox_in_debug(self):
        """get_mycoolpay_service() doit retourner sandbox en mode DEBUG."""
        service = get_mycoolpay_service()
        self.assertIsInstance(service, MyCoolPayService)
        self.assertTrue(service.sandbox)


# ---------------------------------------------------------------------------
# Tests de vérification de signature HMAC webhook
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='test-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='test-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='test-webhook-secret',
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=True,
)
class MyCoolPayWebhookSignatureTest(TestCase):
    """Tests de vérification de signature HMAC pour les webhooks."""

    def setUp(self):
        self.service = MyCoolPayService(sandbox=True)
        self.secret = 'test-webhook-secret'

    def test_valid_signature_accepted(self):
        """Une signature HMAC valide doit être acceptée."""
        payload = b'{"event_type": "payment.success", "transaction_ref": "MCP-123"}'
        signature = _make_hmac_bytes(self.secret, payload)

        self.assertTrue(self.service.verify_webhook_signature(payload, signature))

    def test_invalid_signature_rejected(self):
        """Une signature incorrecte doit être rejetée."""
        payload = b'{"event_type": "payment.success"}'
        self.assertFalse(
            self.service.verify_webhook_signature(payload, 'wrong-signature')
        )

    def test_tampered_payload_rejected(self):
        """Un payload modifié après signature doit être rejeté."""
        original_payload = b'{"amount": 5000}'
        signature = _make_hmac_bytes(self.secret, original_payload)

        tampered_payload = b'{"amount": 1}'
        self.assertFalse(
            self.service.verify_webhook_signature(tampered_payload, signature)
        )

    def test_empty_payload_rejected(self):
        """Un payload vide doit être rejeté."""
        self.assertFalse(self.service.verify_webhook_signature(b'', 'any-sig'))

    def test_empty_signature_rejected(self):
        """Une signature vide doit être rejetée."""
        self.assertFalse(self.service.verify_webhook_signature(b'{"test": 1}', ''))

    def test_missing_webhook_secret_returns_false(self):
        """Sans secret configuré, la vérification doit retourner False."""
        with self.settings(MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=''):
            service = MyCoolPayService.__new__(MyCoolPayService)
            service.sandbox = True
            service.public_key = 'test-pub-key'
            service.private_key = 'test-priv-key'
            service.webhook_secret = ''

            payload = b'{"test": 1}'
            sig = _make_hmac_bytes('any-secret', payload)
            self.assertFalse(service.verify_webhook_signature(payload, sig))

    def test_signature_case_insensitive(self):
        """La comparaison de signature doit être insensible à la casse."""
        payload = b'{"event_type": "payment.success"}'
        signature = _make_hmac_bytes(self.secret, payload)

        # Tester avec signature en majuscules
        self.assertTrue(
            self.service.verify_webhook_signature(payload, signature.upper())
        )


# ---------------------------------------------------------------------------
# Tests de vérification de signature callback
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='test-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='test-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='test-webhook-secret',
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=True,
)
class MyCoolPayCallbackSignatureTest(TestCase):
    """Tests de vérification de signature pour les callbacks."""

    def setUp(self):
        self.service = MyCoolPayService(sandbox=True)
        self.private_key = 'test-priv-key'

    def _build_callback_with_signature(self, data: dict) -> dict:
        """Construire un callback avec signature valide."""
        sorted_items = sorted(data.items())
        data_string = '&'.join(f"{k}={v}" for k, v in sorted_items)
        signature = _make_hmac(self.private_key, data_string)
        return {**data, 'signature': signature}

    def test_valid_callback_signature_accepted(self):
        """Un callback avec signature valide doit être accepté."""
        data = {
            'transaction_ref': 'MCP-123',
            'transaction_status': 'SUCCESS',
            'amount': '5000',
        }
        callback = self._build_callback_with_signature(data)
        self.assertTrue(self.service.verify_callback_signature(callback))

    def test_invalid_callback_signature_rejected(self):
        """Un callback avec signature invalide doit être rejeté."""
        callback = {
            'transaction_ref': 'MCP-123',
            'transaction_status': 'SUCCESS',
            'signature': 'bad-signature',
        }
        self.assertFalse(self.service.verify_callback_signature(callback))

    def test_missing_signature_rejected(self):
        """Un callback sans signature doit être rejeté."""
        callback = {
            'transaction_ref': 'MCP-123',
            'transaction_status': 'SUCCESS',
        }
        self.assertFalse(self.service.verify_callback_signature(callback))


# ---------------------------------------------------------------------------
# Tests de vérification d'IP
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='test-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='test-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='test-webhook-secret',
    MYCOOLPAY_ALLOWED_IPS=['192.168.1.100', '10.0.0.0/24'],
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=False,
)
class MyCoolPayIPVerificationTest(TestCase):
    """Tests de vérification d'adresse IP."""

    def setUp(self):
        self.service = MyCoolPayService(sandbox=True)

    def test_allowed_ip_accepted(self):
        """Une IP autorisée doit être acceptée."""
        self.assertTrue(self.service.verify_callback_ip('192.168.1.100'))

    def test_ip_in_allowed_range_accepted(self):
        """Une IP dans un réseau autorisé doit être acceptée."""
        self.assertTrue(self.service.verify_callback_ip('10.0.0.50'))

    def test_unauthorized_ip_rejected(self):
        """Une IP non autorisée doit être rejetée."""
        self.assertFalse(self.service.verify_callback_ip('1.2.3.4'))

    def test_debug_mode_accepts_all_ips(self):
        """En mode DEBUG, toutes les IPs doivent être acceptées."""
        with self.settings(DEBUG=True):
            self.assertTrue(self.service.verify_callback_ip('1.2.3.4'))


# ---------------------------------------------------------------------------
# Tests des appels API (avec mock HTTP)
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='test-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='test-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='test-webhook-secret',
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=True,
    SITE_URL='http://localhost:8000',
)
class MyCoolPayAPITest(TestCase):
    """Tests des appels à l'API My-CoolPay (avec mock HTTP)."""

    def setUp(self):
        self.service = MyCoolPayService(sandbox=True)

    def _mock_response(self, json_data: dict, status_code: int = 200):
        """Créer un mock de réponse requests."""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.text = json.dumps(json_data)
        return mock_resp

    @patch('requests.post')
    def test_create_paylink_success(self, mock_post):
        """create_paylink doit retourner payment_url et transaction_ref."""
        mock_post.return_value = self._mock_response({
            'payment_url': 'https://pay.my-coolpay.com/pay/abc123',
            'transaction_ref': 'MCP-ABC123',
        })

        result = self.service.create_paylink({
            'transaction_amount': 5000,
            'transaction_currency': 'XAF',
            'transaction_reason': 'Test paiement',
            'app_transaction_ref': 'internal-ref-001',
            'customer_phone_number': '+237690000000',
            'customer_name': 'Jean Dupont',
            'customer_email': 'jean@example.com',
        })

        self.assertEqual(result['payment_url'], 'https://pay.my-coolpay.com/pay/abc123')
        self.assertEqual(result['transaction_ref'], 'MCP-ABC123')
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_create_paylink_missing_field_raises_error(self, mock_post):
        """create_paylink doit lever MyCoolPayError si un champ requis manque."""
        with self.assertRaises(MyCoolPayError) as ctx:
            self.service.create_paylink({
                'transaction_amount': 5000,
                # transaction_currency manquant
                'transaction_reason': 'Test',
                'app_transaction_ref': 'ref-001',
                'customer_phone_number': '+237690000000',
                'customer_name': 'Jean',
                'customer_email': 'jean@example.com',
            })
        self.assertIn('transaction_currency', str(ctx.exception))
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_create_paylink_unsupported_currency_raises_error(self, mock_post):
        """create_paylink doit lever MyCoolPayError pour une devise non supportée."""
        with self.assertRaises(MyCoolPayError) as ctx:
            self.service.create_paylink({
                'transaction_amount': 5000,
                'transaction_currency': 'GBP',  # Non supporté
                'transaction_reason': 'Test',
                'app_transaction_ref': 'ref-001',
                'customer_phone_number': '+237690000000',
                'customer_name': 'Jean',
                'customer_email': 'jean@example.com',
            })
        self.assertIn('GBP', str(ctx.exception))

    @patch('requests.post')
    def test_create_paylink_http_error_raises_mycoolpay_error(self, mock_post):
        """Une erreur HTTP 400+ doit lever MyCoolPayError."""
        mock_post.return_value = self._mock_response(
            {'message': 'Invalid API key'}, status_code=401
        )

        with self.assertRaises(MyCoolPayError):
            self.service.create_paylink({
                'transaction_amount': 5000,
                'transaction_currency': 'XAF',
                'transaction_reason': 'Test',
                'app_transaction_ref': 'ref-001',
                'customer_phone_number': '+237690000000',
                'customer_name': 'Jean',
                'customer_email': 'jean@example.com',
            })

    @patch('requests.get')
    def test_check_transaction_status(self, mock_get):
        """check_transaction_status doit retourner le statut de la transaction."""
        mock_get.return_value = self._mock_response({
            'transaction_status': 'SUCCESS',
            'transaction_ref': 'MCP-123',
            'amount': 5000,
            'currency': 'XAF',
        })

        result = self.service.check_transaction_status('MCP-123')

        self.assertEqual(result['transaction_status'], 'SUCCESS')
        mock_get.assert_called_once()

    @patch('requests.post')
    def test_initiate_payin_unsupported_operator_raises_error(self, mock_post):
        """initiate_payin doit lever MyCoolPayError pour un opérateur non supporté."""
        with self.assertRaises(MyCoolPayError) as ctx:
            self.service.initiate_payin({
                'transaction_amount': 5000,
                'transaction_currency': 'XAF',
                'transaction_reason': 'Test',
                'app_transaction_ref': 'ref-001',
                'customer_phone_number': '+237690000000',
                'customer_name': 'Jean',
                'customer_email': 'jean@example.com',
                'transaction_operator': 'UNKNOWN_OP',
            })
        self.assertIn('UNKNOWN_OP', str(ctx.exception))


# ---------------------------------------------------------------------------
# Tests du paiement d'abonnement
# ---------------------------------------------------------------------------

@override_settings(
    MYCOOLPAY_SANDBOX_PUBLIC_KEY='test-pub-key',
    MYCOOLPAY_SANDBOX_PRIVATE_KEY='test-priv-key',
    MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='test-webhook-secret',
    PAYMENT_SANDBOX_MODE=True,
    DEBUG=True,
    SITE_URL='http://localhost:8000',
)
class MyCoolPaySubscriptionPaymentTest(TestCase):
    """Tests du paiement d'abonnement via My-CoolPay."""

    def setUp(self):
        self.service = MyCoolPayService(sandbox=True)

        self.user = User.objects.create_user(
            email='investor@example.com',
            password='testpass123',
            first_name='Alice',
            last_name='Martin',
        )

        self.plan = SubscriptionPlan.objects.create(
            id='basic_monthly',
            name='BASIC Mensuel',
            price_xaf=Decimal('5000'),
            price_eur=Decimal('7.63'),
            price_usd=Decimal('8.33'),
            duration_days=30,
            max_projects=5,
            features=['analytics'],
        )

    @patch('requests.post')
    def test_process_subscription_payment_success(self, mock_post):
        """process_subscription_payment doit créer un Payment et retourner payment_url."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'payment_url': 'https://pay.my-coolpay.com/pay/sub123',
                'transaction_ref': 'MCP-SUB-123',
            },
            text='{}',
        )

        success, message, data = self.service.process_subscription_payment(
            user=self.user,
            subscription_plan=self.plan,
            phone_number='+237690000000',
            currency='XAF',
        )

        self.assertTrue(success)
        self.assertIn('payment_id', data)
        self.assertIn('payment_url', data)
        self.assertEqual(data['payment_url'], 'https://pay.my-coolpay.com/pay/sub123')

        # Vérifier que le paiement a été créé en base
        payment = Payment.objects.get(id=data['payment_id'])
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.payment_type, Payment.PaymentType.SUBSCRIPTION)
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(payment.currency, 'XAF')
        self.assertEqual(payment.metadata['subscription_plan_id'], 'basic_monthly')

    @patch('requests.post')
    def test_process_subscription_payment_api_error(self, mock_post):
        """process_subscription_payment doit retourner (False, msg, {}) en cas d'erreur API."""
        mock_post.return_value = MagicMock(
            status_code=500,
            json=lambda: {'message': 'Internal Server Error'},
            text='Internal Server Error',
        )

        success, message, data = self.service.process_subscription_payment(
            user=self.user,
            subscription_plan=self.plan,
            phone_number='+237690000000',
            currency='XAF',
        )

        self.assertFalse(success)
        self.assertEqual(data, {})

    def test_process_subscription_payment_empty_phone(self):
        """process_subscription_payment doit échouer avec un numéro vide."""
        success, message, data = self.service.process_subscription_payment(
            user=self.user,
            subscription_plan=self.plan,
            phone_number='',
            currency='XAF',
        )

        self.assertFalse(success)
        self.assertIn('téléphone', message.lower())

    def test_process_subscription_payment_invalid_phone(self):
        """process_subscription_payment doit échouer avec un numéro trop court."""
        success, message, data = self.service.process_subscription_payment(
            user=self.user,
            subscription_plan=self.plan,
            phone_number='123',
            currency='XAF',
        )

        self.assertFalse(success)

    @patch('requests.post')
    def test_process_subscription_payment_normalizes_phone(self, mock_post):
        """process_subscription_payment doit normaliser le numéro sans préfixe +."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'payment_url': 'https://pay.my-coolpay.com/pay/sub456',
                'transaction_ref': 'MCP-SUB-456',
            },
            text='{}',
        )

        success, _, data = self.service.process_subscription_payment(
            user=self.user,
            subscription_plan=self.plan,
            phone_number='690000000',  # Sans préfixe +237
            currency='XAF',
        )

        self.assertTrue(success)

        # Vérifier que le numéro a été normalisé
        payment = Payment.objects.get(id=data['payment_id'])
        self.assertTrue(payment.metadata['phone_number'].startswith('+237'))
