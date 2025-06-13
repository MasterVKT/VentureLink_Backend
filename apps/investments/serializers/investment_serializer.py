"""
Serializers for investment models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.users.serializers import UserSerializer
from apps.projects.serializers import ProjectListSerializer
from apps.investments.models import Investment, InvestmentHistory, InvestmentPayment


class InvestmentPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for InvestmentPayment model.
    """
    
    class Meta:
        model = InvestmentPayment
        fields = [
            'id', 'investment', 'amount', 'currency', 'payment_method',
            'status', 'transaction_id', 'payment_details', 'receipt_file',
            'notes', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestmentPaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an investment payment.
    """
    
    class Meta:
        model = InvestmentPayment
        fields = [
            'amount', 'currency', 'payment_method', 'transaction_id',
            'payment_details', 'receipt_file', 'notes'
        ]
    
    def create(self, validated_data):
        """
        Create and return a new investment payment instance.
        """
        investment_id = self.context.get('investment_id')
        
        return InvestmentPayment.objects.create(
            investment_id=investment_id,
            status=InvestmentPayment.STATUS_PENDING,
            **validated_data
        )


class InvestmentPaymentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an investment payment.
    """
    
    class Meta:
        model = InvestmentPayment
        fields = [
            'status', 'transaction_id', 'payment_details',
            'receipt_file', 'notes'
        ]
    
    def update(self, instance, validated_data):
        """
        Update and process the payment.
        """
        # Update status
        if 'status' in validated_data:
            new_status = validated_data.get('status')
            
            # Set completed timestamp if status is changed to completed
            if new_status == InvestmentPayment.STATUS_COMPLETED and instance.status != new_status:
                instance.completed_at = timezone.now()
        
        return super().update(instance, validated_data)


class InvestmentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for InvestmentHistory model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = InvestmentHistory
        fields = [
            'id', 'investment', 'user', 'old_status', 'new_status',
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InvestmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Investment model with detailed information.
    """
    investor = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor', 'project', 'amount', 'currency',
            'investment_type', 'equity_percentage', 'interest_rate',
            'term_months', 'status', 'description', 'contract_file',
            'notes', 'approved_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'investor', 'project']


class InvestmentListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing investments.
    """
    investor_name = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id', 'investor_name', 'project_title', 'amount', 'currency',
            'investment_type', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_investor_name(self, obj):
        """Get the investor's name."""
        return f"{obj.investor.first_name} {obj.investor.last_name}" if obj.investor else None
    
    def get_project_title(self, obj):
        """Get the project title."""
        return obj.project.title if obj.project else None


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new investment.
    """
    
    class Meta:
        model = Investment
        fields = [
            'amount', 'currency', 'investment_type', 'equity_percentage',
            'interest_rate', 'term_months', 'description', 'contract_file',
            'notes'
        ]
    
    def validate(self, data):
        """
        Custom validation for investment creation.
        """
        investment_type = data.get('investment_type')
        
        # Validate equity investment
        if investment_type == Investment.TYPE_EQUITY:
            if 'equity_percentage' not in data or not data['equity_percentage']:
                raise serializers.ValidationError({
                    'equity_percentage': _('Le pourcentage d\'actions est requis pour un investissement en actions.')
                })
            
        # Validate loan investment
        elif investment_type == Investment.TYPE_LOAN:
            if 'interest_rate' not in data or not data['interest_rate']:
                raise serializers.ValidationError({
                    'interest_rate': _('Le taux d\'intérêt est requis pour un investissement en prêt.')
                })
                
            if 'term_months' not in data or not data['term_months']:
                raise serializers.ValidationError({
                    'term_months': _('La durée du prêt est requise pour un investissement en prêt.')
                })
                
        # Validate convertible note
        elif investment_type == Investment.TYPE_CONVERTIBLE_NOTE:
            if 'interest_rate' not in data or not data['interest_rate']:
                raise serializers.ValidationError({
                    'interest_rate': _('Le taux d\'intérêt est requis pour une note convertible.')
                })
                
            if 'term_months' not in data or not data['term_months']:
                raise serializers.ValidationError({
                    'term_months': _('La durée est requise pour une note convertible.')
                })
                
        return data


class InvestmentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an investment.
    """
    
    class Meta:
        model = Investment
        fields = [
            'amount', 'currency', 'investment_type', 'equity_percentage',
            'interest_rate', 'term_months', 'description', 'contract_file',
            'notes'
        ]
    
    def validate(self, data):
        """
        Custom validation for investment updates.
        """
        # Get current instance for comparison
        instance = self.instance
        
        # If investment is not pending, restrict certain changes
        if instance.status != Investment.STATUS_PENDING:
            for restricted_field in ['amount', 'currency', 'investment_type', 
                                   'equity_percentage', 'interest_rate', 'term_months']:
                if restricted_field in data and data[restricted_field] != getattr(instance, restricted_field):
                    raise serializers.ValidationError({
                        restricted_field: _('Ce champ ne peut pas être modifié une fois que l\'investissement a été approuvé.')
                    })
        
        # Validate based on investment type
        investment_type = data.get('investment_type', instance.investment_type)
        
        if investment_type == Investment.TYPE_EQUITY:
            if 'equity_percentage' in data and not data['equity_percentage']:
                raise serializers.ValidationError({
                    'equity_percentage': _('Le pourcentage d\'actions est requis pour un investissement en actions.')
                })
                
        elif investment_type == Investment.TYPE_LOAN:
            if 'interest_rate' in data and not data['interest_rate']:
                raise serializers.ValidationError({
                    'interest_rate': _('Le taux d\'intérêt est requis pour un investissement en prêt.')
                })
                
            if 'term_months' in data and not data['term_months']:
                raise serializers.ValidationError({
                    'term_months': _('La durée du prêt est requise pour un investissement en prêt.')
                })
        
        return data


class InvestmentStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating the status of an investment.
    """
    status = serializers.ChoiceField(choices=Investment.STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True) 