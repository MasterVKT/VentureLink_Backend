"""
Vues API pour la gestion des médias de projets.
"""

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.projects.models import Project, ProjectMedia
from apps.projects.serializers.project_media_serializer import (
    ProjectMediaSerializer, 
    ProjectMediaCreateSerializer,
    ProjectMediaUpdateSerializer
)
from apps.projects.services.project_media_service import ProjectMediaService
from apps.core.permissions import IsOwnerOrReadOnly


class ProjectMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des médias de projets.
    
    Permet de créer, lire, modifier et supprimer les médias associés aux projets.
    Inclut également des actions pour générer des médias automatiquement.
    """
    
    serializer_class = ProjectMediaSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retourne les médias du projet spécifié dans l'URL"""
        project_id = self.kwargs.get('project_pk')
        if project_id:
            return ProjectMedia.objects.filter(project_id=project_id).order_by('order', '-created_at')
        return ProjectMedia.objects.none()
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return ProjectMediaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectMediaUpdateSerializer
        return ProjectMediaSerializer
    
    def perform_create(self, serializer):
        """Crée un média en associant le projet et le créateur"""
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id)
        
        # Vérifier que l'utilisateur est le créateur du projet
        if project.creator != self.request.user:
            raise PermissionDenied("Vous n'êtes pas autorisé à ajouter des médias à ce projet")
        
        # 🔴 NOUVELLE FONCTIONNALITÉ : Vérifier la limite de médias avant la création
        try:
            serializer.save(project=project)
        except ValidationError as e:
            # Re-lever l'erreur de limite de médias avec un status code approprié
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(str(e))
    
    @swagger_auto_schema(
        method='post',
        operation_description="Génère automatiquement des médias pour le projet",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'source': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['generated', 'unsplash', 'placeholder'],
                    default='generated',
                    description='Source des images à générer'
                ),
                'count': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    default=1,
                    minimum=1,
                    maximum=5,
                    description='Nombre d\'images à générer (max 5)'
                ),
                'overwrite': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    default=False,
                    description='Remplacer les médias existants'
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'stats': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'created': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'total_media': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    ),
                    'media': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            ),
            400: 'Erreur de validation',
            403: 'Permission refusée',
            404: 'Projet non trouvé'
        }
    )
    @action(detail=False, methods=['post'], url_path='generate')
    def generate_media(self, request, project_pk=None):
        """
        Génère automatiquement des médias pour le projet.
        
        Permet de générer des images de placeholder, de télécharger depuis Unsplash,
        ou de créer des placeholders simples.
        """
        project = get_object_or_404(Project, id=project_pk)
        
        # Vérifier que l'utilisateur est le créateur du projet
        if project.creator != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à générer des médias pour ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Valider les paramètres
        source = request.data.get('source', 'generated')
        count = request.data.get('count', 1)
        overwrite = request.data.get('overwrite', False)
        
        # Validation
        if source not in ['generated', 'unsplash', 'placeholder']:
            return Response(
                {'error': 'Source invalide. Utilisez: generated, unsplash, ou placeholder'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(count, int) or count < 1 or count > 5:
            return Response(
                {'error': 'Le nombre doit être un entier entre 1 et 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier s'il y a déjà des médias
        if project.media.exists() and not overwrite:
            return Response(
                {
                    'error': 'Le projet a déjà des médias. Utilisez overwrite=true pour les remplacer',
                    'existing_media_count': project.media.count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Supprimer les médias existants si demandé
            if overwrite:
                project.media.all().delete()
            
            # Générer les médias
            stats = ProjectMediaService._generate_media_for_project(project, count, source)
            
            # Récupérer les médias générés
            new_media = project.media.order_by('-created_at')[:count]
            serializer = ProjectMediaSerializer(new_media, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'message': f'{stats["created"]} média(s) généré(s) avec succès',
                'stats': stats,
                'media': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Définit un média comme image principale du projet",
        responses={
            200: 'Média défini comme principal',
            400: 'Erreur de validation',
            403: 'Permission refusée',
            404: 'Média non trouvé'
        }
    )
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, project_pk=None, pk=None):
        """
        Définit un média comme image principale du projet.
        
        Seules les images peuvent être définies comme principales.
        """
        project = get_object_or_404(Project, id=project_pk)
        media = get_object_or_404(ProjectMedia, id=pk, project=project)
        
        # Vérifier que l'utilisateur est le créateur du projet
        if project.creator != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à modifier ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que c'est une image
        if media.media_type != ProjectMedia.MEDIA_TYPE_IMAGE:
            return Response(
                {'error': 'Seules les images peuvent être définies comme principales'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Désactiver les autres images principales
            ProjectMedia.objects.filter(
                project=project,
                media_type=ProjectMedia.MEDIA_TYPE_IMAGE,
                is_primary=True
            ).update(is_primary=False)
            
            # Activer cette image comme principale
            media.is_primary = True
            media.save()
            
            serializer = ProjectMediaSerializer(media, context={'request': request})
            return Response({
                'success': True,
                'message': 'Média défini comme principal',
                'media': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la mise à jour: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_description="Réorganise l'ordre des médias du projet",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'media_order': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
                            'order': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    ),
                    description='Liste des médias avec leur nouvel ordre'
                )
            },
            required=['media_order']
        ),
        responses={
            200: 'Ordre mis à jour',
            400: 'Erreur de validation',
            403: 'Permission refusée',
            404: 'Projet non trouvé'
        }
    )
    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder_media(self, request, project_pk=None):
        """
        Réorganise l'ordre des médias du projet.
        
        Attend une liste d'objets avec l'ID du média et son nouvel ordre.
        """
        project = get_object_or_404(Project, id=project_pk)
        
        # Vérifier que l'utilisateur est le créateur du projet
        if project.creator != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à modifier ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        media_order = request.data.get('media_order', [])
        
        if not isinstance(media_order, list):
            return Response(
                {'error': 'media_order doit être une liste'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Mettre à jour l'ordre de chaque média
            for item in media_order:
                media_id = item.get('id')
                order = item.get('order')
                
                if not media_id or order is None:
                    continue
                
                ProjectMedia.objects.filter(
                    id=media_id,
                    project=project
                ).update(order=order)
            
            # Récupérer les médias réorganisés
            updated_media = project.media.order_by('order', '-created_at')
            serializer = ProjectMediaSerializer(updated_media, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Ordre mis à jour',
                'media': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la réorganisation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        operation_description="Obtient les informations sur les limites de médias pour l'utilisateur",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'can_add': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'current': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'remaining': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'is_premium': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'upgrade_message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            403: 'Permission refusée',
            404: 'Projet non trouvé'
        }
    )
    @action(detail=False, methods=['get'], url_path='limits')
    def get_media_limits(self, request, project_pk=None):
        """
        Obtient les informations sur les limites de médias pour le projet.
        """
        project = get_object_or_404(Project, id=project_pk)
        
        # Vérifier que l'utilisateur est le créateur du projet
        if project.creator != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à consulter les limites de ce projet'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtenir les informations sur les limites
        limit_info = ProjectMediaService.check_media_limit(project, request.user)
        
        # Ajouter un message pour encourager l'upgrade
        if not limit_info['is_premium'] and limit_info['remaining'] == 0:
            limit_info['upgrade_message'] = (
                f"Passez au compte premium pour avoir jusqu'à {ProjectMediaService.MAX_MEDIA_PREMIUM_USER} médias par projet "
                f"au lieu de {ProjectMediaService.MAX_MEDIA_FREE_USER}."
            )
        elif not limit_info['is_premium']:
            limit_info['upgrade_message'] = (
                f"Compte gratuit : {ProjectMediaService.MAX_MEDIA_FREE_USER} média par projet. "
                f"Passez au premium pour {ProjectMediaService.MAX_MEDIA_PREMIUM_USER} médias."
            )
        else:
            limit_info['upgrade_message'] = f"Compte premium : jusqu'à {ProjectMediaService.MAX_MEDIA_PREMIUM_USER} médias par projet."
        
        return Response(limit_info, status=status.HTTP_200_OK) 