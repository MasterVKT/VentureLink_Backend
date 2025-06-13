"""
Serializers pour les modèles de paiement.
"""
from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.payments.models import Payment, Refund, PaymentPlan, PaymentSubscription, Currency


User = get_user_model()


class RefundSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Refund."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        """Métadonnées du serializer."""
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'currency', 'status', 'status_display',
            'external_refund_id', 'reason', 'notes', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'payment', 'external_refund_id', 'completed_at',
            'created_at', 'updated_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Payment."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    
    class Meta:
        """Métadonnées du serializer."""
        model = Payment
        fields = [
            'id', 'user', 'amount', 'currency', 'status', 'status_display',
            'payment_type', 'payment_type_display', 'external_payment_id',
            'external_checkout_url', 'description', 'metadata', 'completed_at',
            'is_test', 'created_at', 'updated_at', 'refunds',
            'is_completed', 'is_refunded', 'can_be_refunded'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'external_payment_id', 'external_checkout_url',
            'completed_at', 'created_at', 'updated_at', 'refunds',
            'is_completed', 'is_refunded', 'can_be_refunded'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'un paiement."""
    
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text=_('Montant du paiement')
    )
    currency = serializers.CharField(
        max_length=3,
        default='EUR',
        help_text=_('Code de la devise (EUR, USD, etc.)')
    )
    description = serializers.CharField(
        max_length=500,
        help_text=_('Description du paiement')
    )
    payment_type = serializers.ChoiceField(
        choices=Payment.PaymentType.choices,
        default=Payment.PaymentType.OTHER,
        help_text=_('Type de paiement')
    )
    success_url = serializers.URLField(
        required=False,
        allow_null=True,
        help_text=_('URL de redirection après paiement réussi')
    )
    cancel_url = serializers.URLField(
        required=False,
        allow_null=True,
        help_text=_('URL de redirection en cas d\'annulation')
    )
    statement_descriptor = serializers.CharField(
        max_length=22,
        required=False,
        allow_null=True,
        help_text=_('Description qui apparaîtra sur le relevé bancaire (22 caractères max)')
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_('Métadonnées associées au paiement')
    )
    
    def validate_currency(self, value):
        """Valide et normalise la devise."""
        return value.upper()


class RefundCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'un remboursement."""
    
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text=_('Montant à rembourser (si non spécifié, rembourse la totalité)')
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_('Raison du remboursement')
    )
    notes = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text=_('Notes internes sur le remboursement')
    )


class PaymentPlanSerializer(serializers.ModelSerializer):
    """
    Serializer pour les plans d'abonnement.
    """
    features = serializers.JSONField(read_only=True)
    
    class Meta:
        model = PaymentPlan
        fields = [
            'id', 'name', 'description', 'price_xaf', 'price_eur', 'price_usd',
            'billing_cycle', 'trial_days', 'features', 'max_projects', 
            'max_investments', 'priority_support', 'advanced_analytics',
            'is_active', 'is_popular', 'external_plan_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Personnalise la représentation pour inclure le prix dans la devise demandée.
        """
        data = super().to_representation(instance)
        
        # Ajouter le prix selon la devise de l'utilisateur ou la devise par défaut
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Récupérer la devise préférée de l'utilisateur
            user_currency = getattr(request.user, 'preferred_currency', 'XAF')
        else:
            user_currency = 'XAF'
        
        data['price'] = instance.get_price_in_currency(user_currency)
        data['currency'] = user_currency
        data['display_price'] = f"{data['price']} {user_currency}"
        
        return data


class PaymentSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les abonnements.
    """
    plan = PaymentPlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True, required=False)
    user_email = serializers.CharField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PaymentSubscription
        fields = [
            'id', 'user_email', 'plan', 'plan_id', 'status', 'start_date', 
            'end_date', 'next_billing_date', 'auto_renew', 'currency',
            'last_payment', 'external_subscription_id', 'is_active', 
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'is_active', 'days_remaining', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """
        Crée un nouvel abonnement.
        """
        plan_id = validated_data.pop('plan_id', None)
        if plan_id:
            validated_data['plan'] = PaymentPlan.objects.get(id=plan_id)
        
        return super().create(validated_data)


class PaymentSubscriptionCreateSerializer(serializers.Serializer):
    """
    Serializer pour la création d'un abonnement avec paiement.
    """
    plan_id = serializers.UUIDField(required=True)
    currency = serializers.ChoiceField(choices=Currency.choices, default=Currency.XAF)
    payment_method = serializers.CharField(required=True, help_text="ID de la méthode de paiement")
    phone_number = serializers.CharField(required=False, allow_blank=True, help_text="Numéro de téléphone pour Mobile Money")
    success_url = serializers.URLField(required=False, allow_blank=True)
    cancel_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_plan_id(self, value):
        """
        Valide que le plan existe et est actif.
        """
        try:
            plan = PaymentPlan.objects.get(id=value, is_active=True)
            return value
        except PaymentPlan.DoesNotExist:
            raise serializers.ValidationError(_("Plan d'abonnement invalide ou inactif."))
    
    def validate_phone_number(self, value):
        """
        Valide le numéro de téléphone pour les paiements Mobile Money.
        """
        if value and not value.startswith(('+237', '237', '6', '7')):
            raise serializers.ValidationError(_("Format de numéro de téléphone invalide."))
        return value 