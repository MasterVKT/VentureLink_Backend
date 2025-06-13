"""
Serializers for repayment models.
"""
from rest_framework import serializers

from apps.investments.models import Repayment, RepaymentSchedule
from apps.users.serializers import UserSimpleSerializer
from apps.investments.serializers.investment_serializers import InvestmentListSerializer


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    """Serializer for repayment schedule model."""
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'id', 'investment', 'due_date', 'amount', 'principal_amount',
            'interest_amount', 'currency', 'is_paid', 'repayment', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RepaymentScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating repayment schedules."""
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'due_date', 'amount', 'principal_amount', 'interest_amount',
            'currency', 'notes'
        ]


class RepaymentSerializer(serializers.ModelSerializer):
    """Detailed serializer for repayments."""
    investment = InvestmentListSerializer(read_only=True)
    paid_by = UserSimpleSerializer(read_only=True)
    received_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'investment', 'paid_by', 'received_by', 'amount',
            'currency', 'repayment_type', 'principal_amount', 'interest_amount',
            'status', 'transaction_id', 'payment_method', 'payment_details',
            'receipt_file', 'notes', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RepaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for repayment lists."""
    investment = InvestmentListSerializer(read_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'investment', 'amount', 'currency', 'repayment_type',
            'status', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RepaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating repayments."""
    
    class Meta:
        model = Repayment
        fields = [
            'investment', 'amount', 'currency', 'repayment_type',
            'principal_amount', 'interest_amount', 'payment_method',
            'transaction_id', 'payment_details', 'receipt_file', 'notes'
        ]


class RepaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating repayments."""
    
    class Meta:
        model = Repayment
        fields = [
            'amount', 'currency', 'repayment_type', 'principal_amount',
            'interest_amount', 'payment_method', 'transaction_id',
            'payment_details', 'receipt_file', 'notes'
        ]


class RepaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating repayment status."""
    
    class Meta:
        model = Repayment
        fields = ['status'] 