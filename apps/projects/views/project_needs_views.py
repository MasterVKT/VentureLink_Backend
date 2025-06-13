"""
Views for project needs models.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.projects.models.project_needs import ProjectNeeds, ProjectSkillsNeeded
from apps.projects.serializers import (
    ProjectNeedsSerializer, ProjectNeedsCreateSerializer, ProjectNeedsUpdateSerializer,
    ProjectSkillsNeededSerializer, ProjectSkillsNeededCreateSerializer, ProjectSkillsNeededUpdateSerializer
)
from apps.projects.services.project_service import ProjectService


class ProjectNeedsViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectNeeds."""
    queryset = ProjectNeeds.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'resource_type', 'is_critical', 'is_satisfied']
    ordering_fields = ['created_at', 'deadline']
    ordering = ['is_satisfied', 'is_critical', '-created_at']

    def get_queryset(self):
        """
        This view should return needs for the specified project.
        """
        project_id = self.kwargs.get('project_pk')
        if project_id:
            # Check if the project exists and user has permission to view it
            try:
                project = ProjectService.get_project_by_id(
                    project_id=project_id,
                    user=self.request.user if self.request.user.is_authenticated else None
                )
                return ProjectNeeds.objects.filter(project=project)
            except ResourceNotFoundError:
                return ProjectNeeds.objects.none()
        return ProjectNeeds.objects.none()

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return ProjectNeedsCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectNeedsUpdateSerializer
        return ProjectNeedsSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Create a need for a project.
        """
        project_id = self.kwargs.get('project_pk')
        if not project_id:
            return Response(
                {'detail': _('L\'ID du projet est requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the project exists and user is the owner
        try:
            project = ProjectService.get_project_by_id(project_id, request.user)
            if project.creator != request.user:
                return Response(
                    {'detail': _('Vous n\'êtes pas autorisé à ajouter des besoins à ce projet.')},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.context['project_id'] = project_id
        need = serializer.save()
        
        return Response(
            ProjectNeedsSerializer(need).data,
            status=status.HTTP_201_CREATED
        )
        
    def update(self, request, *args, **kwargs):
        """
        Update a need.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user is the project owner
        if instance.project.creator != request.user:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à modifier ce besoin.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        need = serializer.save()
        
        return Response(ProjectNeedsSerializer(need).data)
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete a need.
        """
        instance = self.get_object()
        
        # Check if user is the project owner
        if instance.project.creator != request.user:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer ce besoin.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectSkillsNeededViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectSkillsNeeded."""
    queryset = ProjectSkillsNeeded.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'priority', 'is_satisfied']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'priority', 'name']
    ordering = ['is_satisfied', '-priority', 'name']

    def get_queryset(self):
        """
        This view should return skills needed for the specified project.
        """
        project_id = self.kwargs.get('project_pk')
        if project_id:
            # Check if the project exists and user has permission to view it
            try:
                project = ProjectService.get_project_by_id(
                    project_id=project_id,
                    user=self.request.user if self.request.user.is_authenticated else None
                )
                return ProjectSkillsNeeded.objects.filter(project=project)
            except ResourceNotFoundError:
                return ProjectSkillsNeeded.objects.none()
        return ProjectSkillsNeeded.objects.none()

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return ProjectSkillsNeededCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectSkillsNeededUpdateSerializer
        return ProjectSkillsNeededSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Create a skill needed for a project.
        """
        project_id = self.kwargs.get('project_pk')
        if not project_id:
            return Response(
                {'detail': _('L\'ID du projet est requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the project exists and user is the owner
        try:
            project = ProjectService.get_project_by_id(project_id, request.user)
            if project.creator != request.user:
                return Response(
                    {'detail': _('Vous n\'êtes pas autorisé à ajouter des compétences requises à ce projet.')},
                    status=status.HTTP_403_FORBIDDEN
                )
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        serializer.context['project_id'] = project_id
        skill = serializer.save()
        
        return Response(
            ProjectSkillsNeededSerializer(skill).data,
            status=status.HTTP_201_CREATED
        )
        
    def update(self, request, *args, **kwargs):
        """
        Update a skill needed.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user is the project owner
        if instance.project.creator != request.user:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à modifier cette compétence requise.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        skill = serializer.save()
        
        return Response(ProjectSkillsNeededSerializer(skill).data)
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete a skill needed.
        """
        instance = self.get_object()
        
        # Check if user is the project owner
        if instance.project.creator != request.user:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer cette compétence requise.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 