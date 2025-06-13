from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.investments.models import (
    Investment, InvestmentHistory, InvestmentPayment,
    Repayment, RepaymentSchedule
)


class InvestmentHistoryInline(admin.TabularInline):
    """
    Inline admin for investment history.
    """
    model = InvestmentHistory
    extra = 0
    readonly_fields = ['user', 'old_status', 'new_status', 'comment', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class InvestmentPaymentInline(admin.TabularInline):
    """
    Inline admin for investment payments.
    """
    model = InvestmentPayment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


class RepaymentInline(admin.TabularInline):
    """
    Inline admin for repayments.
    """
    model = Repayment
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fk_name = 'investment'


class RepaymentScheduleInline(admin.TabularInline):
    """
    Inline admin for repayment schedules.
    """
    model = RepaymentSchedule
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for investments.
    """
    list_display = [
        'id', 'investor_email', 'project_title', 'amount', 'currency', 
        'investment_type', 'status', 'created_at'
    ]
    list_filter = ['status', 'investment_type', 'currency', 'created_at']
    search_fields = ['investor__email', 'project__title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [InvestmentHistoryInline, InvestmentPaymentInline, RepaymentInline, RepaymentScheduleInline]
    
    def investor_email(self, obj):
        return obj.investor.email if obj.investor else None
    investor_email.short_description = _('Investisseur')
    
    def project_title(self, obj):
        return obj.project.title if obj.project else None
    project_title.short_description = _('Projet')


@admin.register(InvestmentPayment)
class InvestmentPaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for investment payments.
    """
    list_display = [
        'id', 'investment_ref', 'amount', 'currency', 'payment_method', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['investment__investor__email', 'investment__project__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def investment_ref(self, obj):
        return f"{obj.investment.investor.email} - {obj.investment.project.title}" if obj.investment else None
    investment_ref.short_description = _('Investissement')


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for repayments.
    """
    list_display = [
        'id', 'investment_ref', 'amount', 'currency', 'repayment_type',
        'status', 'created_at'
    ]
    list_filter = ['status', 'repayment_type', 'currency', 'created_at']
    search_fields = ['investment__investor__email', 'investment__project__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def investment_ref(self, obj):
        return f"{obj.investment.investor.email} - {obj.investment.project.title}" if obj.investment else None
    investment_ref.short_description = _('Investissement')


@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    """
    Admin interface for repayment schedules.
    """
    list_display = [
        'id', 'investment_ref', 'due_date', 'amount', 'currency',
        'is_paid', 'created_at'
    ]
    list_filter = ['is_paid', 'currency', 'due_date']
    search_fields = ['investment__investor__email', 'investment__project__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    def investment_ref(self, obj):
        return f"{obj.investment.investor.email} - {obj.investment.project.title}" if obj.investment else None
    investment_ref.short_description = _('Investissement') 