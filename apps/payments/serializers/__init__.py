"""
Serializers pour l'application payments.
"""
from apps.payments.serializers.payment_serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    RefundSerializer, RefundCreateSerializer,
    PaymentPlanSerializer, PaymentSubscriptionSerializer, PaymentSubscriptionCreateSerializer
)

# Nouveaux serializers unifiés
from apps.payments.serializers.subscription_serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionCreateSerializer,
    UserSubscriptionUpdateSerializer
)

# ATTENTION: Ces alias sont DÉPRÉCIÉS
# Utilisez directement les nouveaux serializers
LegacySubscriptionPlanSerializer = PaymentPlanSerializer
LegacySubscriptionSerializer = PaymentSubscriptionSerializer
LegacySubscriptionCreateSerializer = PaymentSubscriptionCreateSerializer

__all__ = [
    # Serializers de paiement
    'PaymentSerializer', 'PaymentCreateSerializer',
    'RefundSerializer', 'RefundCreateSerializer',
    
    # Nouveaux serializers unifiés (UTILISEZ CEUX-CI)
    'SubscriptionPlanSerializer',           # ✅ Plans d'abonnement
    'UserSubscriptionSerializer',           # ✅ Abonnements utilisateur
    'UserSubscriptionCreateSerializer',     # ✅ Création d'abonnement
    'UserSubscriptionUpdateSerializer',     # ✅ Mise à jour d'abonnement
    
    # Serializers dépréciés (à migrer)
    'PaymentPlanSerializer',                # ❌ DÉPRÉCIÉ
    'PaymentSubscriptionSerializer',        # ❌ DÉPRÉCIÉ
    'PaymentSubscriptionCreateSerializer',  # ❌ DÉPRÉCIÉ
    'LegacySubscriptionPlanSerializer',     # ❌ DÉPRÉCIÉ
    'LegacySubscriptionSerializer',         # ❌ DÉPRÉCIÉ
    'LegacySubscriptionCreateSerializer',   # ❌ DÉPRÉCIÉ
] 