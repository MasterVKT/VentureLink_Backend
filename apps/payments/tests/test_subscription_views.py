"""
Tests pour les vues API d'abonnement.
Sprint 3 - B3.4 : Système Abonnements
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from apps.payments.models import SubscriptionPlan, UserSubscription

User = get_user_model()


def make_plan(plan_id, name, price_xaf=5000, price_eur=8, price_usd=9,
              duration_days=30, is_free=False, is_active=True,
              trial_days=0, sort_order=1, max_projects=5,
              max_investments=10, max_messages=50):
    """Helper pour créer un SubscriptionPlan de test."""
    return SubscriptionPlan.objects.create(
        id=plan_id,
        name=name,
        description=f'Plan {name}',
        price_xaf=price_xaf,
        price_eur=price_eur,
        price_usd=price_usd,
        duration_days=duration_days,
        is_free=is_free,
        is_active=is_active,
        trial_days=trial_days,
        sort_order=sort_order,
        max_projects=max_projects,
        max_investments=max_investments,
        max_messages=max_messages,
    )


class SubscriptionPlanListViewTest(TestCase):
    """Tests pour GET /api/v1/payments/plans/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com', password='pass1234'
        )
        self.client.force_authenticate(user=self.user)

        self.free_plan = make_plan('free', 'FREE', price_xaf=0, price_eur=0,
                                   price_usd=0, is_free=True, sort_order=1)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY', sort_order=2)
        self.premium = make_plan('premium_monthly', 'PREMIUM_MONTHLY',
                                 price_xaf=15000, price_eur=23, price_usd=25,
                                 sort_order=3)

    def test_liste_plans_actifs(self):
        url = reverse('payments:subscription-plans')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        self.assertIn('free', ids)
        self.assertIn('basic_monthly', ids)
        self.assertIn('premium_monthly', ids)

    def test_plans_inactifs_exclus(self):
        make_plan('inactive_plan', 'INACTIVE', is_active=False, sort_order=99)
        url = reverse('payments:subscription-plans')
        response = self.client.get(url)
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn('inactive_plan', ids)

    def test_non_authentifie_refuse(self):
        self.client.force_authenticate(user=None)
        url = reverse('payments:subscription-plans')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordre_affichage_respecte(self):
        url = reverse('payments:subscription-plans')
        response = self.client.get(url)
        ids = [p['id'] for p in response.data['results']]
        self.assertEqual(ids.index('free'), 0)
        self.assertLess(ids.index('basic_monthly'), ids.index('premium_monthly'))


class CurrentUserSubscriptionViewTest(TestCase):
    """Tests pour GET /api/v1/payments/subscription/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='sub@example.com', password='pass1234'
        )
        self.client.force_authenticate(user=self.user)
        self.free_plan = make_plan('free', 'FREE', price_xaf=0, price_eur=0,
                                   price_usd=0, is_free=True)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY')

    def test_aucun_abonnement_retourne_message(self):
        url = reverse('payments:user-subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_subscription'])
        self.assertIn('free_plan', response.data)

    def test_abonnement_actif_retourne_donnees(self):
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        url = reverse('payments:user-subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(sub.id))

    def test_abonnement_trial_retourne_donnees(self):
        UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.TRIAL,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=7),
            trial_ends_at=timezone.now() + timezone.timedelta(days=7),
        )
        url = reverse('payments:user-subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'TRIAL')


class SubscribeToPlanViewTest(TestCase):
    """Tests pour POST /api/v1/payments/subscription/subscribe/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='subscribe@example.com', password='pass1234',
            is_premium=False,
        )
        self.client.force_authenticate(user=self.user)
        self.free_plan = make_plan('free', 'FREE', price_xaf=0, price_eur=0,
                                   price_usd=0, is_free=True)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY')
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_souscription_plan_gratuit(self):
        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {'plan_id': 'free', 'billing_currency': 'XAF'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['payment_required'])
        self.assertEqual(response.data['subscription']['status'], 'ACTIVE')

    def test_souscription_plan_inexistant(self):
        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {'plan_id': 'nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_souscription_doublon_refuse(self):
        """Un utilisateur avec un abonnement actif ne peut pas souscrire à nouveau."""
        UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {'plan_id': 'free'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('déjà', response.data['error'])

    def test_souscription_plan_payant_sans_telephone(self):
        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {
            'plan_id': 'basic_monthly',
            'billing_currency': 'XAF',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data['error'])

    @patch('apps.payments.views.subscription_views.get_mycoolpay_service')
    def test_souscription_plan_payant_avec_telephone(self, mock_service):
        """Souscription payante avec My-CoolPay mocké."""
        mock_svc = MagicMock()
        mock_svc.process_subscription_payment.return_value = (
            True,
            'Lien créé',
            {
                'payment_id': 'pay-uuid-123',
                'payment_url': 'https://pay.mycoolpay.com/abc',
                'transaction_ref': 'TXN-001',
            }
        )
        mock_service.return_value = mock_svc

        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {
            'plan_id': 'basic_monthly',
            'billing_currency': 'XAF',
            'phone_number': '+237690000000',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['payment_required'])
        self.assertIn('payment_url', response.data)

    @patch('apps.payments.views.subscription_views.get_mycoolpay_service')
    def test_souscription_echec_mycoolpay_supprime_abonnement(self, mock_service):
        """Si My-CoolPay échoue, l'abonnement PENDING doit être supprimé."""
        mock_svc = MagicMock()
        mock_svc.process_subscription_payment.return_value = (
            False, 'Erreur réseau', {}
        )
        mock_service.return_value = mock_svc

        url = reverse('payments:subscribe-to-plan')
        self.client.post(url, {
            'plan_id': 'basic_monthly',
            'billing_currency': 'XAF',
            'phone_number': '+237690000000',
        })
        # Aucun abonnement ne doit subsister
        self.assertFalse(
            UserSubscription.objects.filter(user=self.user).exists()
        )

    def test_non_authentifie_refuse(self):
        self.client.force_authenticate(user=None)
        url = reverse('payments:subscribe-to-plan')
        response = self.client.post(url, {'plan_id': 'free'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CancelSubscriptionViewTest(TestCase):
    """Tests pour POST /api/v1/payments/subscription/cancel/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='cancel@example.com', password='pass1234',
            is_premium=True,
        )
        self.client.force_authenticate(user=self.user)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY')
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )

    @patch('apps.payments.views.subscription_views.NotificationService')
    def test_annulation_abonnement_actif(self, mock_notif):
        mock_notif.create_from_template.return_value = None
        url = reverse('payments:cancel-subscription')
        response = self.client.post(url, {'reason': 'Test annulation'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('annulé', response.data['message'])

        self.subscription.refresh_from_db()
        self.assertEqual(
            self.subscription.status,
            UserSubscription.SubscriptionStatus.CANCELLED
        )

    def test_annulation_sans_abonnement_actif(self):
        self.subscription.status = UserSubscription.SubscriptionStatus.CANCELLED
        self.subscription.save()
        url = reverse('payments:cancel-subscription')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.payments.views.subscription_views.NotificationService')
    def test_annulation_sans_raison_utilise_defaut(self, mock_notif):
        mock_notif.create_from_template.return_value = None
        url = reverse('payments:cancel-subscription')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UpgradeSubscriptionViewTest(TestCase):
    """Tests pour POST /api/v1/payments/subscription/upgrade/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='upgrade@example.com', password='pass1234',
            is_premium=True,
        )
        self.client.force_authenticate(user=self.user)
        self.free_plan = make_plan('free', 'FREE', price_xaf=0, price_eur=0,
                                   price_usd=0, is_free=True, sort_order=1)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY',
                               price_xaf=5000, sort_order=2)
        self.premium = make_plan('premium_monthly', 'PREMIUM_MONTHLY',
                                 price_xaf=15000, sort_order=3)
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
            billing_currency='XAF',
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_upgrade_sans_abonnement_actif(self):
        self.subscription.status = UserSubscription.SubscriptionStatus.CANCELLED
        self.subscription.save()
        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {'new_plan_id': 'premium_monthly'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upgrade_meme_plan_refuse(self):
        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {
            'new_plan_id': 'basic_monthly',
            'billing_currency': 'XAF',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('déjà', response.data['error'])

    def test_downgrade_vers_free_immediat(self):
        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {
            'new_plan_id': 'free',
            'billing_currency': 'XAF',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['effective'], 'immediate')
        self.assertFalse(response.data['payment_required'])

    def test_downgrade_programme_fin_periode(self):
        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {
            'new_plan_id': 'basic_monthly',
            'billing_currency': 'XAF',
        })
        # Créer un plan moins cher pour tester le downgrade
        cheap = make_plan('starter', 'STARTER', price_xaf=1000, sort_order=0)
        response = self.client.post(url, {
            'new_plan_id': 'starter',
            'billing_currency': 'XAF',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['effective'], 'end_of_period')
        self.assertFalse(response.data['payment_required'])

    @patch('apps.payments.views.subscription_views.get_mycoolpay_service')
    def test_upgrade_vers_plan_plus_cher(self, mock_service):
        mock_svc = MagicMock()
        mock_svc.process_subscription_payment.return_value = (
            True, 'OK', {
                'payment_id': 'pay-upgrade-123',
                'payment_url': 'https://pay.mycoolpay.com/upgrade',
                'transaction_ref': 'TXN-UP-001',
            }
        )
        mock_service.return_value = mock_svc

        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {
            'new_plan_id': 'premium_monthly',
            'billing_currency': 'XAF',
            'phone_number': '+237690000000',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['payment_required'])
        self.assertEqual(response.data['effective'], 'after_payment')

    def test_upgrade_sans_telephone_refuse(self):
        url = reverse('payments:upgrade-subscription')
        response = self.client.post(url, {
            'new_plan_id': 'premium_monthly',
            'billing_currency': 'XAF',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data['error'])


class CheckSubscriptionLimitsViewTest(TestCase):
    """Tests pour GET /api/v1/payments/subscription/limits/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='limits@example.com', password='pass1234'
        )
        self.client.force_authenticate(user=self.user)
        self.free_plan = make_plan('free', 'FREE', price_xaf=0, price_eur=0,
                                   price_usd=0, is_free=True,
                                   max_projects=2, max_investments=5)
        self.basic = make_plan('basic_monthly', 'BASIC_MONTHLY')

    def test_limites_sans_abonnement_utilise_plan_free(self):
        url = reverse('payments:subscription-limits')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan'], 'FREE')
        self.assertIn('projects', response.data['limits'])
        self.assertIn('investments', response.data['limits'])
        self.assertIn('messages', response.data['limits'])

    def test_limites_avec_abonnement_actif(self):
        UserSubscription.objects.create(
            user=self.user,
            plan=self.basic,
            status=UserSubscription.SubscriptionStatus.ACTIVE,
            started_at=timezone.now(),
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
        url = reverse('payments:subscription-limits')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan'], 'BASIC_MONTHLY')

    def test_limites_contient_features(self):
        url = reverse('payments:subscription-limits')
        response = self.client.get(url)
        self.assertIn('features', response.data)
        self.assertIn('ai_matching', response.data['features'])
        self.assertIn('priority_support', response.data['features'])
