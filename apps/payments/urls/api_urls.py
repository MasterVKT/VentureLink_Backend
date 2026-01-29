"""
URLs API pour les paiements
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentViewSet, WebhookViewSet
from apps.payments.views.payment_views import (
    SubscriptionPlanListView, UserSubscriptionView, PaymentHistoryView,
    create_subscription_payment, authorize_payment_otp,
    check_payment_status, get_payment_methods, mycoolpay_callback,
    cancel_subscription, get_account_balance, mycoolpay_webhook
)

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'webhooks', WebhookViewSet, basename='webhook')

app_name = 'payments'

urlpatterns = [
    # URLs du router
    path('', include(router.urls)),
    
    # Plans d'abonnement
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    
    # Abonnement utilisateur
    path('subscription/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('subscription/create/', create_subscription_payment, name='create-subscription-payment'),
    path('subscription/cancel/', cancel_subscription, name='cancel-subscription'),
    
    # Historique des paiements
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    
    # Paiements My-CoolPay (autorisation OTP seulement)
    path('authorize/', authorize_payment_otp, name='authorize-payment-otp'),
    path('<int:payment_id>/status/', check_payment_status, name='check-payment-status'),
    
    # Méthodes de paiement
    path('methods/', get_payment_methods, name='payment-methods'),
    
    # Callback My-CoolPay
    path('mycoolpay/callback/', mycoolpay_callback, name='mycoolpay-callback'),
    path('mycoolpay/webhook/', mycoolpay_webhook, name='mycoolpay-webhook'),
    
    # Balance (admin seulement)
    path('balance/', get_account_balance, name='account-balance'),
] 