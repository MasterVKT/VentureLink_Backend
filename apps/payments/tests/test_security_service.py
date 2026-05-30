"""
Tests pour le service de sécurité des paiements.
Sprint 3 - B3.6 : Logs et Sécurité
"""
import hashlib
import hmac
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.payments.services.security_service import (
    PaymentValidator,
    PaymentRateLimiter,
    PaymentSecurityService,
    PaymentAuditLogger,
    MAX_PAYMENT_ATTEMPTS_PER_HOUR,
    MAX_SUBSCRIPTION_ATTEMPTS_PER_DAY,
)

User = get_user_model()


class PaymentValidatorAmountTest(TestCase):
    """Tests pour la validation des montants."""

    def test_montant_valide_xaf(self):
        valid, error = PaymentValidator.validate_amount(5000, 'XAF')
        self.assertTrue(valid)
        self.assertEqual(error, '')

    def test_montant_valide_eur(self):
        valid, error = PaymentValidator.validate_amount(Decimal('10.00'), 'EUR')
        self.assertTrue(valid)

    def test_montant_zero_invalide(self):
        valid, error = PaymentValidator.validate_amount(0, 'XAF')
        self.assertFalse(valid)
        self.assertIn('supérieur à zéro', error)

    def test_montant_negatif_invalide(self):
        valid, error = PaymentValidator.validate_amount(-100, 'XAF')
        self.assertFalse(valid)

    def test_montant_trop_faible_xaf(self):
        valid, error = PaymentValidator.validate_amount(10, 'XAF')
        self.assertFalse(valid)
        self.assertIn('faible', error)

    def test_montant_trop_eleve_xaf(self):
        valid, error = PaymentValidator.validate_amount(99_000_000, 'XAF')
        self.assertFalse(valid)
        self.assertIn('élevé', error)

    def test_montant_non_numerique(self):
        valid, error = PaymentValidator.validate_amount('abc', 'XAF')
        self.assertFalse(valid)
        self.assertIn('invalide', error)


class PaymentValidatorCurrencyTest(TestCase):
    """Tests pour la validation des devises."""

    def test_devise_xaf_valide(self):
        valid, _ = PaymentValidator.validate_currency('XAF')
        self.assertTrue(valid)

    def test_devise_eur_valide(self):
        valid, _ = PaymentValidator.validate_currency('EUR')
        self.assertTrue(valid)

    def test_devise_usd_valide(self):
        valid, _ = PaymentValidator.validate_currency('USD')
        self.assertTrue(valid)

    def test_devise_inconnue_invalide(self):
        valid, error = PaymentValidator.validate_currency('GBP')
        self.assertFalse(valid)
        self.assertIn('GBP', error)

    def test_devise_vide_invalide(self):
        valid, error = PaymentValidator.validate_currency('')
        self.assertFalse(valid)

    def test_devise_none_invalide(self):
        valid, error = PaymentValidator.validate_currency(None)
        self.assertFalse(valid)

    def test_devise_minuscule_acceptee(self):
        """La validation doit accepter les minuscules (normalisation interne)."""
        valid, _ = PaymentValidator.validate_currency('xaf')
        self.assertTrue(valid)


class PaymentValidatorPhoneTest(TestCase):
    """Tests pour la validation des numéros de téléphone."""

    def test_numero_cameroun_valide(self):
        valid, _ = PaymentValidator.validate_phone_number('+237690000000')
        self.assertTrue(valid)

    def test_numero_france_valide(self):
        valid, _ = PaymentValidator.validate_phone_number('+33612345678')
        self.assertTrue(valid)

    def test_numero_sans_plus_invalide(self):
        valid, error = PaymentValidator.validate_phone_number('237690000000')
        self.assertFalse(valid)
        self.assertIn('+', error)

    def test_numero_vide_invalide(self):
        valid, error = PaymentValidator.validate_phone_number('')
        self.assertFalse(valid)

    def test_numero_trop_court_invalide(self):
        valid, error = PaymentValidator.validate_phone_number('+2376')
        self.assertFalse(valid)
        self.assertIn('court', error)

    def test_numero_trop_long_invalide(self):
        valid, error = PaymentValidator.validate_phone_number('+2376900000001234567')
        self.assertFalse(valid)
        self.assertIn('long', error)

    def test_numero_avec_lettres_invalide(self):
        valid, error = PaymentValidator.validate_phone_number('+237abc000')
        self.assertFalse(valid)
        self.assertIn('chiffres', error)

    def test_numero_avec_espaces_accepte(self):
        """Les espaces doivent être nettoyés avant validation."""
        valid, _ = PaymentValidator.validate_phone_number('+237 690 000 000')
        self.assertTrue(valid)


class PaymentValidatorSignatureTest(TestCase):
    """Tests pour la validation de la signature webhook HMAC."""

    def _make_signature(self, payload: bytes, secret: str) -> str:
        return hmac.new(
            key=secret.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

    def test_signature_valide(self):
        payload = b'{"event":"payment.success"}'
        secret = 'my_webhook_secret'
        sig = self._make_signature(payload, secret)
        self.assertTrue(PaymentValidator.validate_webhook_signature(payload, sig, secret))

    def test_signature_invalide(self):
        payload = b'{"event":"payment.success"}'
        secret = 'my_webhook_secret'
        self.assertFalse(
            PaymentValidator.validate_webhook_signature(payload, 'bad_signature', secret)
        )

    def test_signature_vide_invalide(self):
        payload = b'{"event":"payment.success"}'
        self.assertFalse(
            PaymentValidator.validate_webhook_signature(payload, '', 'secret')
        )

    def test_secret_vide_invalide(self):
        payload = b'{"event":"payment.success"}'
        self.assertFalse(
            PaymentValidator.validate_webhook_signature(payload, 'sig', '')
        )

    def test_payload_modifie_invalide(self):
        """Une signature valide ne doit pas correspondre à un payload modifié."""
        payload = b'{"event":"payment.success"}'
        secret = 'my_webhook_secret'
        sig = self._make_signature(payload, secret)
        tampered = b'{"event":"payment.failed"}'
        self.assertFalse(
            PaymentValidator.validate_webhook_signature(tampered, sig, secret)
        )


class PaymentRateLimiterTest(TestCase):
    """Tests pour le rate limiting des paiements."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='ratelimit@example.com',
            password='testpassword',
        )
        # Vider le cache entre chaque test
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_premiere_tentative_autorisee(self):
        allowed, error = PaymentRateLimiter.check_payment_attempts(self.user)
        self.assertTrue(allowed)
        self.assertEqual(error, '')

    def test_limite_paiement_depassee(self):
        """Après MAX_PAYMENT_ATTEMPTS_PER_HOUR tentatives, la suivante doit être bloquée."""
        for _ in range(MAX_PAYMENT_ATTEMPTS_PER_HOUR):
            PaymentRateLimiter.check_payment_attempts(self.user)

        allowed, error = PaymentRateLimiter.check_payment_attempts(self.user)
        self.assertFalse(allowed)
        self.assertIn('Trop de tentatives', error)

    def test_premiere_souscription_autorisee(self):
        allowed, error = PaymentRateLimiter.check_subscription_attempts(self.user)
        self.assertTrue(allowed)

    def test_limite_souscription_depassee(self):
        for _ in range(MAX_SUBSCRIPTION_ATTEMPTS_PER_DAY):
            PaymentRateLimiter.check_subscription_attempts(self.user)

        allowed, error = PaymentRateLimiter.check_subscription_attempts(self.user)
        self.assertFalse(allowed)
        self.assertIn('Trop de tentatives', error)

    def test_reset_attempts_paiement(self):
        """Après reset, les tentatives doivent être à nouveau autorisées."""
        for _ in range(MAX_PAYMENT_ATTEMPTS_PER_HOUR):
            PaymentRateLimiter.check_payment_attempts(self.user)

        PaymentRateLimiter.reset_attempts(self.user, 'payment')

        allowed, _ = PaymentRateLimiter.check_payment_attempts(self.user)
        self.assertTrue(allowed)


class PaymentSecurityServiceTest(TestCase):
    """Tests pour la façade PaymentSecurityService."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='security@example.com',
            password='testpassword',
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_validation_complete_valide(self):
        valid, error = PaymentSecurityService.validate_payment_request(
            user=self.user,
            amount=5000,
            currency='XAF',
            phone_number='+237690000000',
        )
        self.assertTrue(valid)
        self.assertEqual(error, '')

    def test_validation_devise_invalide(self):
        valid, error = PaymentSecurityService.validate_payment_request(
            user=self.user,
            amount=5000,
            currency='GBP',
            phone_number='+237690000000',
        )
        self.assertFalse(valid)
        self.assertIn('GBP', error)

    def test_validation_montant_invalide(self):
        valid, error = PaymentSecurityService.validate_payment_request(
            user=self.user,
            amount=0,
            currency='XAF',
            phone_number='+237690000000',
        )
        self.assertFalse(valid)

    def test_validation_telephone_invalide(self):
        valid, error = PaymentSecurityService.validate_payment_request(
            user=self.user,
            amount=5000,
            currency='XAF',
            phone_number='0690000000',  # Pas de +
        )
        self.assertFalse(valid)

    def test_get_client_ip_direct(self):
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        ip = PaymentSecurityService.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_forwarded(self):
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 172.16.0.1',
            'REMOTE_ADDR': '192.168.1.1',
        }
        ip = PaymentSecurityService.get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_rate_limit_bloque_validation(self):
        """Le rate limiting doit bloquer avant même la validation devise/montant."""
        cache.clear()
        for _ in range(MAX_PAYMENT_ATTEMPTS_PER_HOUR):
            PaymentRateLimiter.check_payment_attempts(self.user)

        valid, error = PaymentSecurityService.validate_payment_request(
            user=self.user,
            amount=5000,
            currency='XAF',
            phone_number='+237690000000',
        )
        self.assertFalse(valid)
        self.assertIn('Trop de tentatives', error)


class PaymentAuditLoggerTest(TestCase):
    """Tests pour l'audit logger — vérifie que les méthodes s'exécutent sans erreur."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='audit@example.com',
            password='testpassword',
        )

    def test_log_payment_initiated_ne_leve_pas(self):
        """log_payment_initiated ne doit pas lever d'exception."""
        try:
            PaymentAuditLogger.log_payment_initiated(
                user=self.user,
                amount=Decimal('5000'),
                currency='XAF',
                reference='REF-001',
                ip_address='127.0.0.1',
            )
        except Exception as e:
            self.fail(f"log_payment_initiated a levé une exception : {e}")

    def test_log_payment_completed_ne_leve_pas(self):
        try:
            PaymentAuditLogger.log_payment_completed(
                user=self.user,
                payment_id='uuid-123',
                amount=Decimal('5000'),
                currency='XAF',
                reference='REF-001',
            )
        except Exception as e:
            self.fail(f"log_payment_completed a levé une exception : {e}")

    def test_log_payment_failed_ne_leve_pas(self):
        try:
            PaymentAuditLogger.log_payment_failed(
                user=self.user,
                payment_id='uuid-123',
                reason='card_declined',
                ip_address='127.0.0.1',
            )
        except Exception as e:
            self.fail(f"log_payment_failed a levé une exception : {e}")

    def test_log_webhook_received_valide(self):
        try:
            PaymentAuditLogger.log_webhook_received('payment.success', 'REF-001', True)
        except Exception as e:
            self.fail(f"log_webhook_received a levé une exception : {e}")

    def test_log_webhook_received_invalide(self):
        try:
            PaymentAuditLogger.log_webhook_received('payment.success', 'REF-001', False)
        except Exception as e:
            self.fail(f"log_webhook_received (invalide) a levé une exception : {e}")

    def test_log_invalid_signature_ne_leve_pas(self):
        try:
            PaymentAuditLogger.log_invalid_signature('1.2.3.4', '/api/v1/payments/webhook/')
        except Exception as e:
            self.fail(f"log_invalid_signature a levé une exception : {e}")

    def test_log_subscription_action_ne_leve_pas(self):
        try:
            PaymentAuditLogger.log_subscription_action(
                user=self.user,
                action='subscribed_paid',
                plan_name='BASIC_MONTHLY',
                ip_address='127.0.0.1',
            )
        except Exception as e:
            self.fail(f"log_subscription_action a levé une exception : {e}")

    def test_log_rate_limit_exceeded_ne_leve_pas(self):
        try:
            PaymentAuditLogger.log_rate_limit_exceeded(
                user=self.user,
                action='payment_initiation',
                ip_address='127.0.0.1',
            )
        except Exception as e:
            self.fail(f"log_rate_limit_exceeded a levé une exception : {e}")
