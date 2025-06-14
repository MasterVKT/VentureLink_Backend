from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Profile, DomainExpertise, ProjectInterest, Education, Experience, 
    Badge, UserBadge, Subscription, SubscriptionTransaction, DeviceToken,
    CompanyProfile, CompanyMember
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'account_type', 'user_type', 'is_verified', 'is_premium', 'is_active', 'date_joined')
    list_filter = ('account_type', 'user_type', 'is_verified', 'is_premium', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'location')}),
        (_('Account info'), {'fields': ('account_type', 'user_type', 'language', 'preferred_currency')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Status'), {'fields': ('is_verified', 'is_premium', 'fcm_token')}),
        (_('Important dates'), {'fields': ('date_joined',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'account_type', 'user_type'),
        }),
    )


class DomainExpertiseInline(admin.TabularInline):
    model = DomainExpertise
    extra = 0


class ProjectInterestInline(admin.TabularInline):
    model = ProjectInterest
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'verification_level', 'views_count', 'avg_rating', 'created_at')
    list_filter = ('verification_level', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title')
    readonly_fields = ('views_count', 'avg_rating', 'rating_count', 'created_at', 'updated_at')
    inlines = [DomainExpertiseInline, ProjectInterestInline, EducationInline, ExperienceInline, UserBadgeInline]


class CompanyMemberInline(admin.TabularInline):
    model = CompanyMember
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'industry', 'company_size', 'company_stage', 'is_verified', 'created_at')
    list_filter = ('company_size', 'company_stage', 'industry', 'is_verified', 'created_at', 'updated_at')
    search_fields = ('company_name', 'legal_name', 'user__email', 'industry', 'registration_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CompanyMemberInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('user', 'company_name', 'legal_name', 'logo')
        }),
        (_('Legal Information'), {
            'fields': ('registration_number', 'vat_number', 'legal_form'),
            'classes': ('collapse',)
        }),
        (_('Description'), {
            'fields': ('description', 'mission_statement', 'industry', 'specialties')
        }),
        (_('Company Details'), {
            'fields': ('company_size', 'employee_count', 'company_stage', 'founded_year'),
            'classes': ('collapse',)
        }),
        (_('Contact Information'), {
            'fields': ('headquarters_address', 'website', 'linkedin_company', 'twitter_company', 'facebook_company'),
            'classes': ('collapse',)
        }),
        (_('Financial Information'), {
            'fields': ('annual_revenue', 'funding_stage', 'total_funding'),
            'classes': ('collapse',)
        }),
        (_('Verification'), {
            'fields': ('is_verified', 'verification_documents')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CompanyMember)
class CompanyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_profile', 'role', 'title', 'status', 'is_admin', 'start_date')
    list_filter = ('role', 'status', 'is_admin', 'start_date', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'company_profile__company_name', 'title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company_profile', 'user', 'role', 'title')
        }),
        (_('Status'), {
            'fields': ('status', 'is_admin', 'start_date', 'end_date')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'color', 'created_at')
    list_filter = ('badge_type', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('plan', 'status', 'auto_renew', 'start_date', 'end_date')
    search_fields = ('user__email', 'payment_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SubscriptionTransaction)
class SubscriptionTransactionAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'transaction_id', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'payment_method', 'created_at')
    search_fields = ('subscription__user__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'device_name', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active', 'created_at')
    search_fields = ('user__email', 'token', 'device_name')
    readonly_fields = ('created_at', 'updated_at', 'last_used_at') 