"""
Vues pour la gestion des commentaires et likes de commentaires.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Prefetch
from django.utils.translation import gettext_lazy as _

from apps.content.models import Comment, CommentLike
from apps.content.serializers import (
    CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer,
    CommentTreeSerializer, CommentLikeSerializer
)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des commentaires.
    """
    queryset = Comment.objects.select_related('author', 'parent', 'content_type').prefetch_related(
        'likes__user', 'replies'
    )
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action."""
        if self.action == 'create':
            return CommentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CommentUpdateSerializer
        elif self.action in ['list_for_object', 'list_tree']:
            return CommentTreeSerializer
        return CommentSerializer
    
    def get_queryset(self):
        """Filtrer les commentaires actifs."""
        queryset = super().get_queryset().filter(is_active=True)
        
        # Filtrer par type d'objet si spécifié
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        
        if content_type and object_id:
            try:
                app_label, model_name = content_type.split('.')
                ct = ContentType.objects.get_by_natural_key(app_label, model_name)
                queryset = queryset.filter(content_type=ct, object_id=object_id)
            except (ValueError, ContentType.DoesNotExist):
                return queryset.none()
        
        # Filtrer les commentaires parents uniquement si demandé
        if self.request.query_params.get('parent_only', '').lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        return queryset.order_by('-created_at')
    
    def perform_destroy(self, instance):
        """Soft delete - marquer comme inactif au lieu de supprimer."""
        # Vérifier les permissions
        if instance.author != self.request.user and not self.request.user.is_staff:
            return Response(
                {'detail': _('Vous ne pouvez supprimer que vos propres commentaires.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.is_active = False
        instance.save(update_fields=['is_active'])
    
    @action(detail=False, methods=['get'])
    def for_object(self, request):
        """
        Récupère tous les commentaires pour un objet donné.
        Paramètres : content_type, object_id
        """
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        
        if not (content_type and object_id):
            return Response(
                {'detail': _('content_type et object_id sont requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            app_label, model_name = content_type.split('.')
            ct = ContentType.objects.get_by_natural_key(app_label, model_name)
            
            # Vérifier que l'objet existe
            model_class = ct.model_class()
            target_object = get_object_or_404(model_class, id=object_id)
            
        except (ValueError, ContentType.DoesNotExist, model_class.DoesNotExist):
            return Response(
                {'detail': _('Objet introuvable.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les commentaires parents seulement
        comments = Comment.objects.filter(
            content_type=ct,
            object_id=object_id,
            parent__isnull=True,
            is_active=True
        ).select_related('author').prefetch_related(
            Prefetch(
                'replies',
                queryset=Comment.objects.filter(is_active=True).select_related('author')
            ),
            'likes__user'
        ).order_by('-created_at')
        
        serializer = CommentTreeSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """
        Récupère les réponses d'un commentaire.
        """
        comment = self.get_object()
        replies = comment.replies.filter(is_active=True).order_by('created_at')
        serializer = CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Ajouter/retirer un like sur un commentaire.
        """
        comment = self.get_object()
        
        # Vérifier si l'utilisateur a déjà liké
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user
        )
        
        if created:
            return Response(
                {'detail': _('Commentaire liké.'), 'liked': True},
                status=status.HTTP_201_CREATED
            )
        else:
            like.delete()
            return Response(
                {'detail': _('Like retiré.'), 'liked': False},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """
        Signaler un commentaire.
        """
        comment = self.get_object()
        
        # Ne pas permettre de signaler ses propres commentaires
        if comment.author == request.user:
            return Response(
                {'detail': _('Vous ne pouvez pas signaler vos propres commentaires.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment.flag_count += 1
        comment.is_flagged = True
        comment.save(update_fields=['flag_count', 'is_flagged'])
        
        return Response(
            {'detail': _('Commentaire signalé.')},
            status=status.HTTP_200_OK
        )


class CommentLikeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour les likes de commentaires.
    """
    queryset = CommentLike.objects.select_related('user', 'comment')
    serializer_class = CommentLikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par commentaire si spécifié."""
        queryset = super().get_queryset()
        comment_id = self.request.query_params.get('comment_id')
        
        if comment_id:
            queryset = queryset.filter(comment_id=comment_id)
        
        return queryset.order_by('-created_at') 