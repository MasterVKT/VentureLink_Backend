"""
Models initialization for the investments app.
"""
from apps.investments.models.investment import (
    Investment, InvestmentHistory, InvestmentPayment
)
from apps.investments.models.repayment import (
    Repayment, RepaymentSchedule
) 