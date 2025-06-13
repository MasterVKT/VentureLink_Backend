"""
Serializers for investment models.
"""
from rest_framework import serializers

from apps.investments.models import Investment, InvestmentHistory, InvestmentPayment
from apps.users.serializers import UserSimpleSerializer
from apps.projects.serializers import ProjectListSerializer


class InvestmentPaymentSerializer(serializers.ModelSerializer):
    """Serializer for investment payment model."""
    
    class Meta:
        model = InvestmentPayment
        fields = [
            'id', 'investment', 'amount', 'currency', 'payment_method',
            'status', 'transaction_id', 'payment_details', 'receipt_file',
            'notes', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestmentPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating investment payments."""
    
    class Meta:
        model = InvestmentPayment
        fields = [
            'amount', 'currency', 'payment_method', 'transaction_id',
            'payment_details', 'receipt_file', 'notes'
        ]


class InvestmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for investment history."""
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = InvestmentHistory
        fields = [
            'id', 'investment', 'user', 'old_status', 'new_status',
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'investment', 'user', 'old_status', 'new_status', 'created_at']


class InvestmentSerializer(serializers.ModelSerializer):
    """Detailed serializer for investments."""
    investor = UserSimpleSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    payments = InvestmentPaymentSerializer(many=True, read_only=True)
    history = InvestmentHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor', 'project', 'amount', 'currency',
            'investment_type', 'equity_percentage', 'interest_rate',
            'term_months', 'status', 'description', 'contract_file',
            'notes', 'approved_at', 'completed_at', 'created_at',
            'updated_at', 'payments', 'history'
        ]
        read_only_fields = ['id', 'investor', 'created_at', 'updated_at']


class InvestmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for investment lists."""
    investor = UserSimpleSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor', 'project', 'amount', 'currency',
            'investment_type', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating investments."""
    
    class Meta:
        model = Investment
        fields = [
            'project', 'amount', 'currency', 'investment_type',
            'equity_percentage', 'interest_rate', 'term_months',
            'description'
        ]


class InvestmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating investments."""
    
    class Meta:
        model = Investment
        fields = [
            'amount', 'currency', 'investment_type', 'equity_percentage',
            'interest_rate', 'term_months', 'description', 'contract_file',
            'notes'
        ]


class InvestmentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating investment status."""
    comment = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = Investment
        fields = ['status', 'comment'] 