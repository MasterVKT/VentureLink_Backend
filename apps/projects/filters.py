"""
Filtres personnalisés pour l'application projects.
"""
import django_filters
from django.db import models
from .models import Project, ProjectCategory, ProjectTag


class BooleanChoiceFilter(django_filters.BooleanFilter):
    """
    Filtre booléen personnalisé qui gère la conversion des strings vers booléens.
    """
    
    def filter(self, qs, value):
        if value is not None:
            # Convertir les chaînes en booléens
            if isinstance(value, str):
                value = value.lower().strip()
                if value in ['true', '1', 'yes', 'on']:
                    value = True
                elif value in ['false', '0', 'no', 'off']:
                    value = False
                else:
                    # Ignorer les valeurs invalides
                    return qs
            
            return super().filter(qs, value)
        return qs


class ProjectFilter(django_filters.FilterSet):
    """
    Filterset personnalisé pour les projets avec gestion des types.
    """
    
    # Filtres booléens sécurisés
    is_featured = BooleanChoiceFilter(field_name='is_featured')
    is_premium = BooleanChoiceFilter(field_name='is_premium')
    is_verified = BooleanChoiceFilter(field_name='is_verified')
    is_draft = BooleanChoiceFilter(field_name='is_draft')
    
    # Autres filtres
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    stage = django_filters.CharFilter(field_name='stage', lookup_expr='iexact')
    location_country = django_filters.CharFilter(field_name='location_country', lookup_expr='iexact')
    location_city = django_filters.CharFilter(field_name='location_city', lookup_expr='icontains')
    
    # Filtres numériques
    funding_min = django_filters.NumberFilter(field_name='funding_min', lookup_expr='gte')
    funding_max = django_filters.NumberFilter(field_name='funding_max', lookup_expr='lte')
    
    # Filtres de relation
    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=ProjectCategory.objects.filter(is_active=True)
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=ProjectTag.objects.filter(is_active=True)
    )
    creator = django_filters.NumberFilter(field_name='creator__id')
    
    # Filtres de date
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Project
        fields = [
            'category', 'stage', 'is_premium', 'is_featured', 'is_verified',
            'status', 'location_country', 'location_city', 'tags', 
            'funding_min', 'funding_max', 'creator', 'is_draft',
            'published_after', 'published_before',
            'created_after', 'created_before'
        ] 