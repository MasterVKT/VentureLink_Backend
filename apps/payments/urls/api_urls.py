"""
URLs API pour les paiements et abonnements.
Sprint 3 - B3.4 : Système Abonnements
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentViewSet, WebhookViewSet
from apps.payments.views.payment_views import (
    PaymentHistoryView,
    create_subscription_payment,
    authorize_payment_otp,
    check_payment_status,
    get_payment_methods,
    mycoolpay_callback,
    get_account_balance,
    mycoolpay_webhook,
)
# Nouvelles vues d'abonnement (B3.4)
from apps.payments.views.subscription_views import (
    SubscriptionPlanListView,
    SubscriptionPlanDetailView,
    CurrentUserSubscriptionView,
    subscribe_to_plan,
    upgrade_subscription,
    cancel_subscription,
    check_subscription_limits,
)

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'webhooks', WebhookViewSet, basename='webhook')

app_name = 'payments'

urlpatterns = [
    # URLs du router (paiements CRUD)
    path('', include(router.urls)),

    # -----------------------------------------------------------------------
    # Plans d'abonnement (B3.4)
    # -----------------------------------------------------------------------
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('plans/<str:id>/', SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),

    # -----------------------------------------------------------------------
    # Abonnement utilisateur (B3.4)
    # -----------------------------------------------------------------------
    # GET  — abonnement actif de l'utilisateur
    path('subscription/', CurrentUserSubscriptionView.as_view(), name='user-subscription'),
    # POST — souscrire à un plan
    path('subscription/subscribe/', subscribe_to_plan, name='subscribe-to-plan'),
    # POST — upgrade ou downgrade
    path('subscription/upgrade/', upgrade_subscription, name='upgrade-subscription'),
    # POST — annuler l'abonnement
    path('subscription/cancel/', cancel_subscription, name='cancel-subscription'),
    # GET  — vérifier les limites du plan actif
    path('subscription/limits/', check_subscription_limits, name='subscription-limits'),

    # Compatibilité ascendante avec l'ancienne route de création
    path('subscription/create/', create_subscription_payment, name='create-subscription-payment'),

    # -----------------------------------------------------------------------
    # Historique des paiements
    # -----------------------------------------------------------------------
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),

    # -----------------------------------------------------------------------
    # Paiements My-CoolPay
    # -----------------------------------------------------------------------
    path('authorize/', authorize_payment_otp, name='authorize-payment-otp'),
    path('<int:payment_id>/status/', check_payment_status, name='check-payment-status'),
    path('methods/', get_payment_methods, name='payment-methods'),
    path('mycoolpay/callback/', mycoolpay_callback, name='mycoolpay-callback'),
    path('mycoolpay/webhook/', mycoolpay_webhook, name='mycoolpay-webhook'),

    # -----------------------------------------------------------------------
    # Administration
    # -----------------------------------------------------------------------
    path('balance/', get_account_balance, name='account-balance'),
]
