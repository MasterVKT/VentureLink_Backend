"""
Vues pour la gestion des publications, médias et likes de publications.
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend

from apps.content.models import Publication, PublicationMedia, PublicationLike
from apps.content.serializers import (
    PublicationSerializer, PublicationCreateSerializer, PublicationUpdateSerializer,
    PublicationListSerializer, PublicationMediaSerializer, PublicationLikeSerializer
)
from apps.content.filters import PublicationFilter


class PublicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des publications.
    """
    queryset = Publication.objects.select_related('author').prefetch_related(
        'media', 'likes__user'
    )
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PublicationFilter
    search_fields = ['title', 'content', 'summary', 'tags']
    ordering_fields = ['created_at', 'published_at', 'views_count', 'likes_count']
    ordering = ['-published_at', '-created_at']
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action."""
        if self.action == 'create':
            return PublicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PublicationUpdateSerializer
        elif self.action == 'list':
            return PublicationListSerializer
        return PublicationSerializer
    
    def get_queryset(self):
        """Filtrer les publications selon les permissions."""
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que les publications publiées
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                status=Publication.STATUS_PUBLISHED,
                published_at__isnull=False
            )
        
        # Filtrer par auteur si spécifié
        author_id = self.request.query_params.get('author_id')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Créer une publication."""
        # Vérifier que l'utilisateur est admin
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied(
                _("Seuls les administrateurs peuvent créer des publications.")
            )
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        """Mettre à jour une publication."""
        # Vérifier les permissions
        if not (self.request.user == serializer.instance.author or self.request.user.is_staff):
            raise permissions.PermissionDenied(
                _("Vous ne pouvez modifier que vos propres publications.")
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer une publication."""
        # Vérifier les permissions
        if not (self.request.user == instance.author or self.request.user.is_staff):
            raise permissions.PermissionDenied(
                _("Vous ne pouvez supprimer que vos propres publications.")
            )
        instance.delete()
    
    def retrieve(self, request, *args, **kwargs):
        """Récupérer une publication et incrémenter les vues."""
        instance = self.get_object()
        
        # Incrémenter le compteur de vues
        instance.increment_views()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Récupère les publications mises en avant.
        """
        publications = self.get_queryset().filter(is_featured=True)[:10]
        serializer = PublicationListSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pinned(self, request):
        """
        Récupère les publications épinglées.
        """
        publications = self.get_queryset().filter(is_pinned=True)
        serializer = PublicationListSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Récupère les publications par type.
        Paramètre: type
        """
        publication_type = request.query_params.get('type')
        if not publication_type:
            return Response(
                {'detail': _('Le paramètre type est requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        publications = self.get_queryset().filter(publication_type=publication_type)
        
        page = self.paginate_queryset(publications)
        if page is not None:
            serializer = PublicationListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicationListSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_domain(self, request):
        """
        Récupère les publications par domaine.
        Paramètre: domain
        """
        domain = request.query_params.get('domain')
        if not domain:
            return Response(
                {'detail': _('Le paramètre domain est requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        publications = self.get_queryset().filter(domain=domain)
        
        page = self.paginate_queryset(publications)
        if page is not None:
            serializer = PublicationListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicationListSerializer(publications, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Ajouter/retirer un like sur une publication.
        """
        publication = self.get_object()
        
        # Vérifier si l'utilisateur a déjà liké
        like, created = PublicationLike.objects.get_or_create(
            publication=publication,
            user=request.user
        )
        
        if created:
            return Response(
                {'detail': _('Publication likée.'), 'liked': True},
                status=status.HTTP_201_CREATED
            )
        else:
            like.delete()
            return Response(
                {'detail': _('Like retiré.'), 'liked': False},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Incrémenter le compteur de partages.
        """
        publication = self.get_object()
        publication.shares_count += 1
        publication.save(update_fields=['shares_count'])
        
        return Response(
            {'detail': _('Publication partagée.'), 'shares_count': publication.shares_count},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def admin_stats(self, request):
        """
        Statistiques des publications pour les administrateurs.
        """
        total_publications = Publication.objects.count()
        published_publications = Publication.objects.filter(
            status=Publication.STATUS_PUBLISHED
        ).count()
        draft_publications = Publication.objects.filter(
            status=Publication.STATUS_DRAFT
        ).count()
        
        stats = {
            'total_publications': total_publications,
            'published_publications': published_publications,
            'draft_publications': draft_publications,
            'featured_publications': Publication.objects.filter(is_featured=True).count(),
            'sponsored_publications': Publication.objects.filter(is_sponsored=True).count(),
        }
        
        return Response(stats)


class PublicationMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des médias de publication.
    """
    queryset = PublicationMedia.objects.select_related('publication')
    serializer_class = PublicationMediaSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Filtrer par publication si spécifié."""
        queryset = super().get_queryset()
        publication_id = self.request.query_params.get('publication_id')
        
        if publication_id:
            queryset = queryset.filter(publication_id=publication_id)
        
        return queryset.order_by('order')
    
    def perform_create(self, serializer):
        """Créer un média de publication."""
        publication = get_object_or_404(
            Publication, 
            id=self.request.data.get('publication_id')
        )
        
        # Vérifier les permissions
        if not (self.request.user == publication.author or self.request.user.is_staff):
            raise permissions.PermissionDenied(
                _("Vous ne pouvez ajouter des médias qu'à vos propres publications.")
            )
        
        # Vérifier le nombre de médias (max 3)
        if publication.media.count() >= 3:
            raise permissions.PermissionDenied(
                _("Une publication ne peut avoir plus de 3 médias.")
            )
        
        serializer.save(publication=publication)
    
    def perform_update(self, serializer):
        """Mettre à jour un média de publication."""
        # Vérifier les permissions
        if not (self.request.user == serializer.instance.publication.author or 
                self.request.user.is_staff):
            raise permissions.PermissionDenied(
                _("Vous ne pouvez modifier que les médias de vos propres publications.")
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """Supprimer un média de publication."""
        # Vérifier les permissions
        if not (self.request.user == instance.publication.author or self.request.user.is_staff):
            raise permissions.PermissionDenied(
                _("Vous ne pouvez supprimer que les médias de vos propres publications.")
            )
        instance.delete()


class PublicationLikeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour les likes de publications.
    """
    queryset = PublicationLike.objects.select_related('user', 'publication')
    serializer_class = PublicationLikeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Filtrer par publication si spécifié."""
        queryset = super().get_queryset()
        publication_id = self.request.query_params.get('publication_id')
        
        if publication_id:
            queryset = queryset.filter(publication_id=publication_id)
        
        return queryset.order_by('-created_at') 
