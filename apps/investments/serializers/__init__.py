"""
Serializers initialization for the investments app.
"""
from apps.investments.serializers.investment_serializers import (
    InvestmentSerializer, InvestmentListSerializer,
    InvestmentCreateSerializer, InvestmentUpdateSerializer,
    InvestmentStatusUpdateSerializer, InvestmentPaymentSerializer,
    InvestmentPaymentCreateSerializer, InvestmentHistorySerializer
)
from apps.investments.serializers.repayment_serializers import (
    RepaymentSerializer, RepaymentListSerializer,
    RepaymentCreateSerializer, RepaymentUpdateSerializer,
    RepaymentStatusUpdateSerializer, RepaymentScheduleSerializer,
    RepaymentScheduleCreateSerializer
) 