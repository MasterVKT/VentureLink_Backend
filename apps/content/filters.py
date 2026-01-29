"""
Filtres personnalisés pour l'application content.
"""
import django_filters
from django.db import models
from .models import Publication


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


class PublicationFilter(django_filters.FilterSet):
    """
    Filterset personnalisé pour les publications avec gestion des types.
    """
    
    # Filtres booléens sécurisés
    is_featured = BooleanChoiceFilter(field_name='is_featured')
    is_sponsored = BooleanChoiceFilter(field_name='is_sponsored')
    is_pinned = BooleanChoiceFilter(field_name='is_pinned')
    
    # Autres filtres
    publication_type = django_filters.CharFilter(field_name='publication_type', lookup_expr='iexact')
    domain = django_filters.CharFilter(field_name='domain', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    author_id = django_filters.NumberFilter(field_name='author__id')
    
    # Filtres de date
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Publication
        fields = [
            'publication_type', 'domain', 'status', 'is_featured', 
            'is_sponsored', 'is_pinned', 'author_id',
            'published_after', 'published_before',
            'created_after', 'created_before'
        ] 