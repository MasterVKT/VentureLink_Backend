"""
Configuration de l'administration pour l'application analytics.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.analytics.models import (
    UserMetrics, ProjectMetrics, DailyMetrics,
    EventLog, ReferralTracker
)


@admin.register(UserMetrics)
class UserMetricsAdmin(admin.ModelAdmin):
    """Administration des métriques utilisateur."""
    
    list_display = (
        'user', 'projects_created_count', 'total_project_views',
        'investments_made_count', 'total_investment_amount', 'login_count'
    )
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('created_at',)
    readonly_fields = (
        'created_at', 'updated_at', 'projects_created_count',
        'projects_published_count', 'total_project_views',
        'total_project_interests', 'total_comments_received',
        'investments_made_count', 'total_investment_amount',
        'messages_sent_count', 'messages_received_count',
        'last_login', 'login_count'
    )
    
    fieldsets = (
        (_('Utilisateur'), {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        (_('Projets'), {
            'fields': ('projects_created_count', 'projects_published_count')
        }),
        (_('Engagement'), {
            'fields': ('total_project_views', 'total_project_interests', 'total_comments_received')
        }),
        (_('Investissements'), {
            'fields': ('investments_made_count', 'total_investment_amount')
        }),
        (_('Messagerie'), {
            'fields': ('messages_sent_count', 'messages_received_count')
        }),
        (_('Connexion'), {
            'fields': ('last_login', 'login_count')
        }),
    )


@admin.register(ProjectMetrics)
class ProjectMetricsAdmin(admin.ModelAdmin):
    """Administration des métriques de projet."""
    
    list_display = (
        'content_type', 'object_id', 'view_count',
        'interest_count', 'investment_count', 'total_investment_amount'
    )
    search_fields = ('object_id',)
    list_filter = ('content_type', 'created_at')
    readonly_fields = (
        'content_type', 'object_id', 'created_at', 'updated_at',
        'view_count', 'interest_count', 'favorite_count',
        'comment_count', 'share_count', 'investment_count',
        'total_investment_amount', 'view_to_interest_rate',
        'interest_to_investment_rate'
    )
    
    fieldsets = (
        (_('Projet'), {
            'fields': ('content_type', 'object_id', 'created_at', 'updated_at')
        }),
        (_('Métriques de base'), {
            'fields': ('view_count', 'interest_count', 'favorite_count')
        }),
        (_('Interaction'), {
            'fields': ('comment_count', 'share_count')
        }),
        (_('Investissement'), {
            'fields': ('investment_count', 'total_investment_amount')
        }),
        (_('Conversion'), {
            'fields': ('view_to_interest_rate', 'interest_to_investment_rate')
        }),
    )


@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    """Administration des métriques quotidiennes."""
    
    list_display = (
        'date', 'new_users_count', 'active_users_count',
        'new_projects_count', 'published_projects_count',
        'total_views_count', 'total_investment_amount'
    )
    list_filter = ('date',)
    readonly_fields = (
        'created_at', 'updated_at', 'new_users_count',
        'active_users_count', 'new_projects_count',
        'published_projects_count', 'total_views_count',
        'total_interests_count', 'total_investment_amount',
        'new_subscriptions_count', 'subscription_revenue'
    )
    
    fieldsets = (
        (_('Date'), {
            'fields': ('date', 'created_at', 'updated_at')
        }),
        (_('Utilisateurs'), {
            'fields': ('new_users_count', 'active_users_count')
        }),
        (_('Projets'), {
            'fields': ('new_projects_count', 'published_projects_count')
        }),
        (_('Engagement'), {
            'fields': ('total_views_count', 'total_interests_count')
        }),
        (_('Finances'), {
            'fields': ('total_investment_amount', 'new_subscriptions_count', 'subscription_revenue')
        }),
    )


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    """Administration du journal d'événements."""
    
    list_display = (
        'event_type', 'user', 'content_type',
        'object_id', 'created_at', 'ip_address'
    )
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = (
        'event_type', 'user', 'content_type', 'object_id',
        'metadata', 'ip_address', 'user_agent', 'created_at',
        'updated_at'
    )
    
    fieldsets = (
        (_('Événement'), {
            'fields': ('event_type', 'created_at', 'updated_at')
        }),
        (_('Utilisateur'), {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        (_('Objet concerné'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Données supplémentaires'), {
            'fields': ('metadata',)
        }),
    )


@admin.register(ReferralTracker)
class ReferralTrackerAdmin(admin.ModelAdmin):
    """Administration du suivi des référencements."""
    
    list_display = (
        'source', 'referrer', 'utm_campaign',
        'user', 'action', 'created_at'
    )
    list_filter = ('source', 'utm_campaign', 'utm_medium', 'created_at')
    search_fields = ('user__email', 'source', 'utm_campaign')
    readonly_fields = (
        'source', 'referrer', 'utm_source', 'utm_medium',
        'utm_campaign', 'utm_term', 'utm_content',
        'user', 'action', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        (_('Référencement'), {
            'fields': ('source', 'referrer', 'created_at', 'updated_at')
        }),
        (_('Paramètres UTM'), {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content')
        }),
        (_('Utilisateur'), {
            'fields': ('user', 'action', 'ip_address', 'user_agent')
        }),
    )
