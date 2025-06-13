from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models.user import User
from .models.profile import Profile
from .models.subscription import Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_premium', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_premium', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'user_type')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'is_premium')}),
        (_('Preferences'), {'fields': ('language', 'preferred_currency')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'first_name', 'last_name'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'verification_level', 'created_at')
    list_filter = ('verification_level',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio_short', 'title')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User information'), {'fields': ('user', 'created_at', 'updated_at')}),
        (_('Profile details'), {'fields': ('profile_picture', 'cover_picture', 'title', 'bio_short')}),
        (_('Professional information'), {'fields': ('website', 'social_linkedin', 'social_twitter', 'social_facebook')}),
        (_('Statistics'), {'fields': ('views_count', 'avg_rating', 'rating_count')}),
        (_('Verification'), {'fields': ('verification_level',)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('plan', 'status', 'auto_renew')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User information'), {'fields': ('user',)}),
        (_('Subscription details'), {'fields': ('plan', 'status', 'start_date', 'end_date', 'auto_renew')}),
        (_('Payment information'), {'fields': ('payment_provider', 'payment_id')}),
        (_('Dates'), {'fields': ('created_at', 'updated_at')}),
    ) 