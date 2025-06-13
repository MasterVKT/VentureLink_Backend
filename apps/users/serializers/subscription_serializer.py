"""
Sérialiseurs pour les abonnements et paiements.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models.subscription import Subscription, SubscriptionTransaction


class FeatureSerializer(serializers.Serializer):
    """
    Sérialiseur pour les fonctionnalités d'un plan d'abonnement.
    """
    name = serializers.CharField()
    description = serializers.CharField()
    included = serializers.BooleanField()
    limit = serializers.IntegerField(allow_null=True)


class SubscriptionPlanSerializer(serializers.Serializer):
    """
    Sérialiseur pour les plans d'abonnement.
    """
    id = serializers.CharField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    billing_cycle = serializers.CharField()
    features = FeatureSerializer(many=True)


class SubscriptionTransactionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les transactions d'abonnement.
    """
    receipt_url = serializers.SerializerMethodField()
    transaction_date = serializers.DateTimeField(source='created_at')
    
    class Meta:
        model = SubscriptionTransaction
        fields = [
            'id', 'amount', 'currency', 'transaction_id', 
            'status', 'payment_method', 'transaction_date', 'receipt_url'
        ]
    
    def get_receipt_url(self, obj):
        """
        Retourne l'URL du reçu si disponible.
        """
        # Dans une implémentation réelle, on pourrait retourner une URL
        # générée dynamiquement ou stockée en base de données
        return None


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les abonnements.
    """
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'start_date', 
            'end_date', 'auto_renew', 'payment_provider', 'payment_id'
        ]
        read_only_fields = fields


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de l'abonnement.
    """
    class Meta:
        model = Subscription
        fields = ['auto_renew']


class SubscriptionCheckoutSerializer(serializers.Serializer):
    """
    Sérialiseur pour la création d'un checkout d'abonnement.
    """
    plan = serializers.ChoiceField(
        choices=['PREMIUM_MONTHLY', 'PREMIUM_YEARLY'],
        required=True
    )
    return_url = serializers.URLField(required=False)
    
    def validate_plan(self, value):
        if value not in ['PREMIUM_MONTHLY', 'PREMIUM_YEARLY']:
            raise serializers.ValidationError(_('Plan non valide. Choisissez entre PREMIUM_MONTHLY ou PREMIUM_YEARLY.'))
        return value


class AutoRenewSerializer(serializers.Serializer):
    """
    Sérialiseur pour la mise à jour du renouvellement automatique.
    """
    auto_renew = serializers.BooleanField()


class SubscriptionCancelSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'annulation d'un abonnement.
    """
    cancel_reason = serializers.CharField(required=False, allow_null=True, allow_blank=True) 