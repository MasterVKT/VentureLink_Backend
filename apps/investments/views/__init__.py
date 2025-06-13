"""
Views initialization for the investments app.
"""
from apps.investments.views.investment_views import (
    InvestmentViewSet, InvestmentPaymentViewSet
)
from apps.investments.views.repayment_views import (
    RepaymentViewSet, RepaymentScheduleViewSet
) 