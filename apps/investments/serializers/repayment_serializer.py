"""
Serializers for repayment models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.serializers import UserSerializer
from apps.investments.serializers.investment_serializer import InvestmentListSerializer
from apps.investments.models import Repayment, RepaymentSchedule


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for RepaymentSchedule model.
    """
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'id', 'investment', 'due_date', 'amount', 'principal_amount',
            'interest_amount', 'currency', 'is_paid', 'repayment',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RepaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Repayment model.
    """
    paid_by = UserSerializer(read_only=True)
    received_by = UserSerializer(read_only=True)
    investment = InvestmentListSerializer(read_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'investment', 'paid_by', 'received_by', 'amount',
            'currency', 'repayment_type', 'principal_amount',
            'interest_amount', 'status', 'transaction_id',
            'payment_method', 'payment_details', 'receipt_file',
            'notes', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RepaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new repayment.
    """
    
    class Meta:
        model = Repayment
        fields = [
            'amount', 'currency', 'repayment_type', 'principal_amount',
            'interest_amount', 'payment_method', 'transaction_id',
            'payment_details', 'receipt_file', 'notes'
        ]
    
    def validate(self, data):
        """
        Custom validation for creating a repayment.
        """
        repayment_type = data.get('repayment_type')
        
        # For mixed type, ensure both principal and interest are provided
        if repayment_type == Repayment.TYPE_MIXED:
            principal_amount = data.get('principal_amount')
            interest_amount = data.get('interest_amount')
            
            if not principal_amount:
                raise serializers.ValidationError({
                    'principal_amount': _('Le montant du principal est requis pour ce type de remboursement.')
                })
                
            if not interest_amount:
                raise serializers.ValidationError({
                    'interest_amount': _('Le montant des intérêts est requis pour ce type de remboursement.')
                })
                
            # Verify that principal + interest = total amount
            total_amount = data.get('amount')
            calculated_total = principal_amount + interest_amount
            
            if total_amount != calculated_total:
                raise serializers.ValidationError(
                    _('La somme du principal et des intérêts doit être égale au montant total.')
                )
                
        return data
    
    def create(self, validated_data):
        """
        Create and return a new repayment instance.
        """
        investment_id = self.context.get('investment_id')
        user = self.context['request'].user
        
        # Get investment to set received_by
        investment = Investment.objects.get(id=investment_id)
        
        return Repayment.objects.create(
            investment_id=investment_id,
            paid_by=user,
            received_by=investment.investor,
            status=Repayment.STATUS_PENDING,
            **validated_data
        )


class RepaymentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a repayment.
    """
    
    class Meta:
        model = Repayment
        fields = [
            'status', 'transaction_id', 'payment_details',
            'receipt_file', 'notes'
        ]
    
    def update(self, instance, validated_data):
        """
        Update and process the repayment.
        """
        from django.utils import timezone
        
        # Update status
        if 'status' in validated_data:
            new_status = validated_data.get('status')
            
            # Set completed timestamp if status is changed to completed
            if new_status == Repayment.STATUS_COMPLETED and instance.status != new_status:
                instance.completed_at = timezone.now()
                
                # If this repayment is linked to a schedule item, mark it as paid
                if hasattr(instance, 'schedule_item'):
                    instance.schedule_item.is_paid = True
                    instance.schedule_item.save()
        
        return super().update(instance, validated_data)


class RepaymentScheduleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a repayment schedule.
    """
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'due_date', 'amount', 'principal_amount',
            'interest_amount', 'currency', 'notes'
        ]
    
    def validate(self, data):
        """
        Custom validation for creating a repayment schedule.
        """
        # Verify that principal + interest = total amount
        principal_amount = data.get('principal_amount')
        interest_amount = data.get('interest_amount')
        total_amount = data.get('amount')
        
        if principal_amount and interest_amount:
            calculated_total = principal_amount + interest_amount
            
            if total_amount != calculated_total:
                raise serializers.ValidationError(
                    _('La somme du principal et des intérêts doit être égale au montant total.')
                )
                
        return data
    
    def create(self, validated_data):
        """
        Create and return a new repayment schedule instance.
        """
        investment_id = self.context.get('investment_id')
        
        return RepaymentSchedule.objects.create(
            investment_id=investment_id,
            is_paid=False,
            **validated_data
        )


class RepaymentScheduleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a repayment schedule.
    """
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'due_date', 'amount', 'principal_amount',
            'interest_amount', 'currency', 'is_paid', 'notes'
        ]
        
    def validate(self, data):
        """
        Custom validation for updating a repayment schedule.
        """
        # Only allow is_paid to be set to True manually (not other fields) if there's a linked repayment
        instance = self.instance
        if instance.repayment and 'is_paid' in data and data['is_paid']:
            allowed_fields = ['is_paid', 'notes']
            for field in data:
                if field not in allowed_fields:
                    raise serializers.ValidationError({
                        field: _('Ce champ ne peut pas être modifié car un remboursement est déjà associé.')
                    })
                    
        # Verify that principal + interest = total amount if any of these fields change
        amount_fields = ['amount', 'principal_amount', 'interest_amount']
        if any(field in data for field in amount_fields):
            principal_amount = data.get('principal_amount', instance.principal_amount)
            interest_amount = data.get('interest_amount', instance.interest_amount)
            total_amount = data.get('amount', instance.amount)
            
            calculated_total = principal_amount + interest_amount
            
            if total_amount != calculated_total:
                raise serializers.ValidationError(
                    _('La somme du principal et des intérêts doit être égale au montant total.')
                )
                
        return data 