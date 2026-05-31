"""
Configuration de l'interface d'administration pour l'application payments.
Sprint 3 - B3.4 : Ajout de SubscriptionPlan et UserSubscription
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone

from apps.payments.models import Payment, Refund, SubscriptionPlan, UserSubscription


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
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _("Montant")

    def has_add_permission(self, request):
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
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _("Montant")

    def has_add_permission(self, request):
        return False


# ---------------------------------------------------------------------------
# Plans d'abonnement (B3.4)
# ---------------------------------------------------------------------------

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Administration des plans d'abonnement."""
    list_display = [
        'id', 'name', 'price_xaf_display', 'price_eur_display',
        'duration_days', 'is_active', 'is_popular', 'is_free', 'sort_order',
    ]
    list_filter = ['is_active', 'is_popular', 'is_free', 'ai_matching', 'priority_support']
    search_fields = ['id', 'name', 'description']
    list_editable = ['is_active', 'is_popular', 'sort_order']
    ordering = ['sort_order']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (_('Informations générales'), {
            'fields': ('id', 'name', 'description', 'is_active', 'is_popular', 'is_free', 'sort_order')
        }),
        (_('Prix multi-devises'), {
            'fields': ('price_xaf', 'price_eur', 'price_usd')
        }),
        (_('Durée et essai'), {
            'fields': ('duration_days', 'trial_days')
        }),
        (_('Limites'), {
            'fields': ('max_projects', 'max_investments', 'max_messages')
        }),
        (_('Fonctionnalités'), {
            'fields': ('ai_matching', 'priority_support', 'advanced_analytics', 'custom_branding', 'features')
        }),
        (_('Intégration My-CoolPay'), {
            'fields': ('mycoolpay_plan_id',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_xaf_display(self, obj):
        return obj.format_price('XAF')
    price_xaf_display.short_description = _("Prix XAF")

    def price_eur_display(self, obj):
        return obj.format_price('EUR')
    price_eur_display.short_description = _("Prix EUR")


# ---------------------------------------------------------------------------
# Abonnements utilisateurs (B3.4)
# ---------------------------------------------------------------------------

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """Administration des abonnements utilisateurs."""
    list_display = [
        'id', 'user_email', 'plan_name', 'status', 'billing_currency',
        'started_at', 'expires_at', 'days_remaining_display',
        'auto_renew', 'is_active_display',
    ]
    list_filter = ['status', 'billing_currency', 'auto_renew', 'plan']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'plan__name']
    readonly_fields = [
        'id', 'user', 'started_at', 'last_payment_date', 'last_payment_amount',
        'mycoolpay_subscription_id', 'created_at', 'updated_at',
        'is_active', 'is_in_trial', 'is_expired', 'days_remaining',
    ]
    date_hierarchy = 'started_at'
    ordering = ['-started_at']

    fieldsets = (
        (_('Utilisateur et plan'), {
            'fields': ('id', 'user', 'plan', 'status', 'billing_currency')
        }),
        (_('Dates'), {
            'fields': ('started_at', 'expires_at', 'trial_ends_at', 'cancelled_at', 'suspended_at')
        }),
        (_('Renouvellement'), {
            'fields': ('auto_renew', 'next_billing_date')
        }),
        (_('Paiements'), {
            'fields': ('last_payment_date', 'last_payment_amount', 'mycoolpay_subscription_id')
        }),
        (_('État calculé'), {
            'fields': ('is_active', 'is_in_trial', 'is_expired', 'days_remaining'),
            'classes': ('collapse',)
        }),
        (_('Notes et métadonnées'), {
            'fields': ('admin_notes', 'metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['action_cancel_subscriptions', 'action_suspend_subscriptions']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _("Utilisateur")
    user_email.admin_order_field = 'user__email'

    def plan_name(self, obj):
        return obj.plan.name
    plan_name.short_description = _("Plan")
    plan_name.admin_order_field = 'plan__name'

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color:red;">Expiré</span>')
        elif days <= 7:
            return format_html('<span style="color:orange;">{} j</span>', days)
        return format_html('<span style="color:green;">{} j</span>', days)
    days_remaining_display.short_description = _("Jours restants")

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">✓ Actif</span>')
        return format_html('<span style="color:red;">✗ Inactif</span>')
    is_active_display.short_description = _("Actif")

    @admin.action(description=_("Annuler les abonnements sélectionnés"))
    def action_cancel_subscriptions(self, request, queryset):
        count = 0
        for subscription in queryset.filter(
            status__in=[
                UserSubscription.SubscriptionStatus.ACTIVE,
                UserSubscription.SubscriptionStatus.TRIAL,
            ]
        ):
            subscription.cancel(reason='Annulation administrative')
            count += 1
        self.message_user(request, f"{count} abonnement(s) annulé(s).")

    @admin.action(description=_("Suspendre les abonnements sélectionnés"))
    def action_suspend_subscriptions(self, request, queryset):
        count = 0
        for subscription in queryset.filter(
            status=UserSubscription.SubscriptionStatus.ACTIVE
        ):
            subscription.suspend(reason='Suspension administrative')
            count += 1
        self.message_user(request, f"{count} abonnement(s) suspendu(s).")

    def has_add_permission(self, request):
        return False
