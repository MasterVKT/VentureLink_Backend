"""
Configuration de l'interface d'administration pour l'application payments.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from apps.payments.models import Payment, Refund


class RefundInline(admin.TabularInline):
    """Affichage des remboursements associés à un paiement."""
    model = Refund
    extra = 0
    readonly_fields = [
        'id', 'status', 'amount', 'currency', 'external_refund_id',
        'completed_at', 'created_at', 'updated_at'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Désactive l'ajout de remboursements via l'admin."""
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les paiements."""
    list_display = [
        'id', 'user', 'amount_with_currency', 'payment_type', 'status',
        'is_test', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'payment_type', 'is_test', 'currency']
    search_fields = ['id', 'user__email', 'user__first_name', 'user__last_name', 'description']
    readonly_fields = [
        'id', 'user', 'content_type', 'object_id', 'external_payment_id',
        'external_checkout_url', 'completed_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    inlines = [RefundInline]
    
    def amount_with_currency(self, obj):
        """Affiche le montant avec la devise."""
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _("Montant")
    
    def has_add_permission(self, request):
        """Désactive l'ajout de paiements via l'admin."""
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Configuration de l'interface d'administration pour les remboursements."""
    list_display = [
        'id', 'payment', 'amount_with_currency', 'status',
        'created_at', 'completed_at'
    ]
    list_filter = ['status', 'currency']
    search_fields = ['id', 'payment__id', 'reason', 'notes']
    readonly_fields = [
        'id', 'payment', 'external_refund_id', 'completed_at',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    def amount_with_currency(self, obj):
        """Affiche le montant avec la devise."""
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _("Montant")
    
    def has_add_permission(self, request):
        """Désactive l'ajout de remboursements via l'admin."""
        return False
