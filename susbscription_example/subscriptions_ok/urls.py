from django.urls import path
from . import views

urlpatterns = [
    path('subscriptions/initiate/', views.InitiateSubscriptionView.as_view(), name='initiate-subscription'),
    path('payment/callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
    path('subscriptions/update-status/', views.UpdatePremiumStatusView.as_view(), name='update-premium-status'),
    path('subscriptions/activate-coach/', views.ActivateCoachSubscriptionView.as_view(), name='activate-coach-subscription'),
]