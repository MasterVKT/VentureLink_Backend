"""
Tests des vues API de paiement (Tâche B3.7).

Couvre :
- GET  /api/v1/payments/plans/              → liste des plans
- GET  /api/v1/payments/subscription/       → abonnement actif
- POST /api/v1/payments/subscription/create/ → créer paiement abonnement
- POST /api/v1/payments/subscription/cancel/ → annuler abonnement
- GET  /api/v1/payments/history/            → historique paiements
- GET  /api/v1/payments/methods/            → méthodes de paiement
- GET  /api/v1/payments/balance/            → solde (admin)
- GET  /api/v1/payments/payments/           → liste paiements (ViewSet)
- GET  /api/v1/payments/payments/{id}/      → détail paiement
- Authentification requise sur tous les endpoints protégés
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.payments.models import Payment, Refund, SubscriptionPlan, UserSubscription

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(email='user@test.com', password='testpass123', is_staff=False):
    """Créer un utilisateur de test."""
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
        is_staff=is_staff,
    )


def create_plan(plan_id='basic_monthly', name='BASIC Mensuel', price_xaf=5000,
                price_eur=Decimal('7.63'), price_usd=Decimal('8.33'),
                duration_days=30, is_active=True):
    """Créer un plan d'abonnement de test."""
    return SubscriptionPlan.objects.create(
        id=plan_id,
        name=name,
        price_xaf=Decimal(str(price_xaf)),
        price_eur=price_eur,
        price_usd=price_usd,
        duration_days=duration_days,
        is_active=is_active,
        features=[],
    )


def create_payment(user, amount=Decimal('5000.00'), currency='XAF',
                   payment_type=Payment.PaymentType.SUBSCRIPTION,
                   status_val=Payment.PaymentStatus.PENDING,
                   external_id='MCP-TEST-001'):
    """Créer un paiement de test."""
    return Payment.objects.create(
        user=user,
        amount=amount,
        currency=currency,
        description='Test paiement',
        payment_type=payment_type,
        status=status_val,
        external_payment_id=external_id,
        metadata={},
    )


# ---------------------------------------------------------------------------
# Tests — Plans d'abonnement
# ---------------------------------------------------------------------------

class SubscriptionPlanListViewTest(TestCase):
    """Tests de GET /api/v1/payments/plans/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.plan_active = create_plan('basic_monthly', 'BASIC Mensuel')
        self.plan_inactive = create_plan('premium_monthly', 'PREMIUM Mensuel',
                                         is_active=False)

    def test_list_returns_only_active_plans(self):
        """Seuls les plans actifs doivent être retournés."""
        response = self.client.get('/api/v1/payments/plans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        self.assertIn('basic_monthly', ids)
        self.assertNotIn('premium_monthly', ids)

    def test_plan_contains_required_fields(self):
        """Chaque plan doit contenir les champs requis."""
        response = self.client.get('/api/v1/payments/plans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        plan = response.data['results'][0]
        required_fields = [
            'id', 'name', 'price_xaf', 'price_eur', 'price_usd',
            'duration_days', 'features', 'is_active',
        ]
        for field in required_fields:
            self.assertIn(field, plan, f"Champ manquant: {field}")

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/payments/plans/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_multiple_plans_ordered_by_price(self):
        """Les plans doivent être ordonnés par prix XAF croissant."""
        create_plan('free_plan', 'FREE', price_xaf=0)
        response = self.client.get('/api/v1/payments/plans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [p['price_xaf'] for p in response.data['results']]
        self.assertEqual(prices, sorted(prices))


# ---------------------------------------------------------------------------
# Tests — Abonnement utilisateur
# ---------------------------------------------------------------------------

class UserSubscriptionViewTest(TestCase):
    """Tests de GET /api/v1/payments/subscription/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.plan = create_plan()

    def test_no_subscription_returns_no_subscription_message(self):
        """Sans abonnement actif, retourner un message approprié."""
        response = self.client.get('/api/v1/payments/subscription/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('has_subscription', True))

    def test_active_subscription_returned(self):
        """Un abonnement actif doit être retourné avec ses détails."""
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        response = self.client.get('/api/v1/payments/subscription/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(sub.id))
        self.assertIn('plan', response.data)
        self.assertIn('status', response.data)

    def test_trial_subscription_returned(self):
        """Un abonnement en période d'essai doit aussi être retourné."""
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.TRIAL,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=7),
            trial_ends_at=timezone.now() + timezone.timedelta(days=7),
        )
        response = self.client.get('/api/v1/payments/subscription/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'TRIAL')

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/payments/subscription/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests — Création paiement abonnement
# ---------------------------------------------------------------------------

class CreateSubscriptionPaymentViewTest(TestCase):
    """Tests de POST /api/v1/payments/subscription/create/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.plan = create_plan()

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService.create_paylink')
    def test_create_subscription_payment_success(self, mock_paylink):
        """La création d'un paiement d'abonnement doit retourner 201 avec payment_url."""
        mock_paylink.return_value = {
            'payment_url': 'https://pay.my-coolpay.com/pay/abc123',
            'transaction_ref': 'MCP-ABC123',
        }
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'plan_id': 'basic_monthly',
            'phone_number': '+237690000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment_url', response.data)
        self.assertIn('payment_id', response.data)
        self.assertIn('transaction_ref', response.data)
        self.assertIn('plan', response.data)

    def test_missing_plan_id_returns_400(self):
        """Sans plan_id, retourner 400."""
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_missing_phone_number_returns_400(self):
        """Sans phone_number, retourner 400."""
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'plan_id': 'basic_monthly',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_plan_id_returns_404(self):
        """Un plan_id inexistant doit retourner 404."""
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'plan_id': 'nonexistent_plan',
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_already_active_subscription_returns_400(self):
        """Un utilisateur avec abonnement actif ne peut pas en créer un autre."""
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'plan_id': 'basic_monthly',
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/payments/subscription/create/', {
            'plan_id': 'basic_monthly',
            'phone_number': '+237690000000',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests — Annulation abonnement
# ---------------------------------------------------------------------------

class CancelSubscriptionViewTest(TestCase):
    """Tests de POST /api/v1/payments/subscription/cancel/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.plan = create_plan()

    def test_cancel_active_subscription_success(self):
        """L'annulation d'un abonnement actif doit retourner 200."""
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        with patch(
            'apps.notifications.services.notification_service'
            '.NotificationService.create_from_template'
        ):
            response = self.client.post('/api/v1/payments/subscription/cancel/', {
                'reason': 'Test annulation',
            }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_cancel_without_subscription_returns_404(self):
        """Annuler sans abonnement actif doit retourner 404."""
        response = self.client.post('/api/v1/payments/subscription/cancel/', {},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_status_becomes_cancelled(self):
        """Après annulation, le statut doit être CANCELLED."""
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        with patch(
            'apps.notifications.services.notification_service'
            '.NotificationService.create_from_template'
        ):
            self.client.post('/api/v1/payments/subscription/cancel/', {}, format='json')

        sub.refresh_from_db()
        self.assertEqual(sub.status, UserSubscription.SubscriptionStatus.CANCELLED)
        self.assertIsNotNone(sub.cancelled_at)


# ---------------------------------------------------------------------------
# Tests — Historique des paiements
# ---------------------------------------------------------------------------

class PaymentHistoryViewTest(TestCase):
    """Tests de GET /api/v1/payments/history/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.other_user = create_user(email='other@test.com')
        self.client.force_authenticate(user=self.user)

    def test_returns_only_user_payments(self):
        """L'historique ne doit contenir que les paiements de l'utilisateur."""
        create_payment(self.user, external_id='MCP-USER-001')
        create_payment(self.other_user, external_id='MCP-OTHER-001')

        response = self.client.get('/api/v1/payments/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_payments_ordered_by_date_desc(self):
        """Les paiements doivent être ordonnés du plus récent au plus ancien."""
        p1 = create_payment(self.user, external_id='MCP-001')
        p2 = create_payment(self.user, external_id='MCP-002')

        response = self.client.get('/api/v1/payments/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        # p2 créé après p1, doit apparaître en premier
        self.assertEqual(ids[0], str(p2.id))

    def test_empty_history_returns_empty_list(self):
        """Un utilisateur sans paiements doit recevoir une liste vide."""
        response = self.client.get('/api/v1/payments/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/payments/history/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests — Méthodes de paiement
# ---------------------------------------------------------------------------

class PaymentMethodsViewTest(TestCase):
    """Tests de GET /api/v1/payments/methods/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_returns_mycoolpay_method(self):
        """La liste des méthodes doit contenir My-CoolPay."""
        response = self.client.get('/api/v1/payments/methods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('methods', response.data)
        codes = [m['code'] for m in response.data['methods']]
        self.assertIn('MYCOOLPAY', codes)

    def test_returns_supported_currencies(self):
        """La réponse doit inclure les devises supportées."""
        response = self.client.get('/api/v1/payments/methods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('supported_currencies', response.data)
        currencies = response.data['supported_currencies']
        self.assertIn('XAF', currencies)
        self.assertIn('EUR', currencies)

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/payments/methods/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests — Solde compte (admin)
# ---------------------------------------------------------------------------

class AccountBalanceViewTest(TestCase):
    """Tests de GET /api/v1/payments/balance/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.admin = create_user(email='admin@test.com', is_staff=True)

    def test_non_admin_returns_403(self):
        """Un utilisateur non-admin doit recevoir 403."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/payments/balance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.payments.services.mycoolpay_service.MyCoolPayService._make_request')
    def test_admin_can_access_balance(self, mock_request):
        """Un admin doit pouvoir accéder au solde."""
        mock_request.return_value = {'balance': 100000, 'currency': 'XAF'}
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/payments/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_returns_401(self):
        """Un utilisateur non authentifié doit recevoir 401."""
        response = self.client.get('/api/v1/payments/balance/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Tests — PaymentViewSet (liste et détail)
# ---------------------------------------------------------------------------

class PaymentViewSetTest(TestCase):
    """Tests du PaymentViewSet GET /api/v1/payments/payments/"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.other_user = create_user(email='other@test.com')
        self.client.force_authenticate(user=self.user)

    def test_list_returns_user_payments_only(self):
        """La liste ne doit contenir que les paiements de l'utilisateur."""
        p = create_payment(self.user, external_id='MCP-MINE')
        create_payment(self.other_user, external_id='MCP-OTHER')

        response = self.client.get('/api/v1/payments/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(p.id), ids)
        self.assertEqual(len(ids), 1)

    def test_retrieve_own_payment(self):
        """Un utilisateur peut récupérer ses propres paiements."""
        p = create_payment(self.user, external_id='MCP-MINE-2')
        response = self.client.get(f'/api/v1/payments/payments/{p.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(p.id))

    def test_retrieve_other_user_payment_returns_404(self):
        """Un utilisateur ne peut pas accéder aux paiements d'un autre."""
        p = create_payment(self.other_user, external_id='MCP-OTHER-2')
        response = self.client.get(f'/api/v1/payments/payments/{p.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_sees_all_payments(self):
        """Un admin peut voir tous les paiements."""
        admin = create_user(email='admin@test.com', is_staff=True)
        self.client.force_authenticate(user=admin)
        create_payment(self.user, external_id='MCP-U1')
        create_payment(self.other_user, external_id='MCP-U2')

        response = self.client.get('/api/v1/payments/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 2)

    def test_filter_by_status(self):
        """Le filtre par statut doit fonctionner."""
        create_payment(self.user, status_val=Payment.PaymentStatus.COMPLETED,
                       external_id='MCP-DONE')
        create_payment(self.user, status_val=Payment.PaymentStatus.PENDING,
                       external_id='MCP-PEND')

        response = self.client.get('/api/v1/payments/payments/?status=COMPLETED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['status'], 'COMPLETED')

    def test_payment_detail_contains_required_fields(self):
        """Le détail d'un paiement doit contenir les champs requis."""
        p = create_payment(self.user, external_id='MCP-DETAIL')
        response = self.client.get(f'/api/v1/payments/payments/{p.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        required = ['id', 'amount', 'currency', 'status', 'payment_type',
                    'created_at', 'is_completed', 'can_be_refunded']
        for field in required:
            self.assertIn(field, response.data, f"Champ manquant: {field}")


# ---------------------------------------------------------------------------
# Tests — Webhook endpoint HTTP
# ---------------------------------------------------------------------------

class WebhookEndpointSecurityTest(TestCase):
    """Tests de sécurité de l'endpoint POST /api/v1/payments/mycoolpay/webhook/"""

    def setUp(self):
        self.client = APIClient()

    def _sign(self, body: str, secret: str) -> str:
        import hmac, hashlib
        return hmac.new(
            key=secret.encode('utf-8'),
            msg=body.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).hexdigest()

    @patch('apps.payments.services.webhook_service.WebhookService.process_webhook_event',
           return_value=True)
    def test_valid_signature_returns_200(self, mock_process):
        """Un webhook signé correctement doit retourner 200."""
        secret = 'test-webhook-secret-sandbox'
        body = json.dumps({'event_type': 'payment.success', 'transaction_ref': 'MCP-001'})
        sig = self._sign(body, secret)

        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=secret,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=body,
                content_type='application/json',
                HTTP_X_MYCOOLPAY_SIGNATURE=sig,
            )
        self.assertEqual(response.status_code, 200)

    def test_no_signature_returns_403(self):
        """Sans signature, retourner 403."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='some-secret',
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=json.dumps({'event_type': 'payment.success'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 403)

    def test_wrong_signature_returns_403(self):
        """Une signature incorrecte doit retourner 403."""
        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET='correct-secret',
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=json.dumps({'event_type': 'payment.success'}),
                content_type='application/json',
                HTTP_X_MYCOOLPAY_SIGNATURE='wrong-signature',
            )
        self.assertEqual(response.status_code, 403)

    def test_invalid_json_returns_400(self):
        """Un JSON invalide avec signature valide doit retourner 400."""
        secret = 'test-secret'
        body = 'not-json'
        sig = self._sign(body, secret)

        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=secret,
            PAYMENT_SANDBOX_MODE=True,
        ):
            response = self.client.post(
                '/api/v1/payments/mycoolpay/webhook/',
                data=body,
                content_type='application/json',
                HTTP_X_MYCOOLPAY_SIGNATURE=sig,
            )
        self.assertEqual(response.status_code, 400)

    def test_no_auth_required_for_webhook(self):
        """Le webhook ne doit pas exiger d'authentification JWT."""
        secret = 'test-secret'
        body = json.dumps({'event_type': 'payment.success', 'transaction_ref': 'X'})
        sig = self._sign(body, secret)

        with self.settings(
            MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=secret,
            PAYMENT_SANDBOX_MODE=True,
        ):
            with patch(
                'apps.payments.services.webhook_service.WebhookService.process_webhook_event',
                return_value=True,
            ):
                response = self.client.post(
                    '/api/v1/payments/mycoolpay/webhook/',
                    data=body,
                    content_type='application/json',
                    HTTP_X_MYCOOLPAY_SIGNATURE=sig,
                )
        # Pas de 401 — le webhook est public (sécurisé par HMAC)
        self.assertNotEqual(response.status_code, 401)
