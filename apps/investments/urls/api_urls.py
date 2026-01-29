"""
URL patterns for investment API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from apps.investments.views import (
    InvestmentViewSet, InvestmentPaymentViewSet,
    RepaymentViewSet, RepaymentScheduleViewSet
)
from rest_framework.permissions import AllowAny

# Router principal
router = DefaultRouter()
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'payments', InvestmentPaymentViewSet, basename='payment')
router.register(r'repayments', RepaymentViewSet, basename='repayment')
router.register(r'schedules', RepaymentScheduleViewSet, basename='schedule')

# Router imbriqué pour les paiements d'investissement
investments_router = NestedDefaultRouter(router, r'investments', lookup='investment')
investments_router.register(r'payments', InvestmentPaymentViewSet, basename='investment-payment')
investments_router.register(r'repayments', RepaymentViewSet, basename='investment-repayment')
investments_router.register(r'schedules', RepaymentScheduleViewSet, basename='investment-schedule')

urlpatterns = [
    # Route directe pour les statistiques générales (sans authentification)
    path('stats/', InvestmentViewSet.as_view({'get': 'general_stats'}, permission_classes=[AllowAny]), name='investment-stats'),
    path('', include(router.urls)),
    path('', include(investments_router.urls)),
] 