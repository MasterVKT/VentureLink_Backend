"""
Modèles de données pour l'application payments.
Modèles unifiés pour résoudre la confusion entre PaymentPlan/SubscriptionPlan.
"""

# Nouveaux modèles unifiés (à utiliser en priorité)
from .subscription_plan import SubscriptionPlan
from .user_subscription import UserSubscription

# Modèles existants de paiement
from .payment import (
    Payment, 
    Refund, 
    Currency, 
    PaymentMethod,
    PaymentPlan,        # DÉPRÉCIÉ - utiliser SubscriptionPlan
    PaymentSubscription # DÉPRÉCIÉ - utiliser UserSubscription
)

# Alias pour compatibilité avec le code existant
PaymentStatus = Payment.PaymentStatus
RefundStatus = Refund.RefundStatus

# ATTENTION: Ces alias sont DÉPRÉCIÉS et seront supprimés
# Utilisez directement SubscriptionPlan et UserSubscription
LegacyPaymentPlan = PaymentPlan
LegacyPaymentSubscription = PaymentSubscription

__all__ = [
    # Modèles principaux (UTILISEZ CEUX-CI)
    'SubscriptionPlan',       # ✅ Plan d'abonnement unifié
    'UserSubscription',       # ✅ Abonnement utilisateur unifié
    
    # Modèles de paiement
    'Payment',
    'Refund', 
    'PaymentMethod',
    'Currency',
    
    # Status helpers
    'PaymentStatus',
    'RefundStatus',
    
    # Modèles dépréciés (à migrer)
    'PaymentPlan',           # ❌ DÉPRÉCIÉ
    'PaymentSubscription',   # ❌ DÉPRÉCIÉ
    'LegacyPaymentPlan',     # ❌ DÉPRÉCIÉ
    'LegacyPaymentSubscription', # ❌ DÉPRÉCIÉ
] 