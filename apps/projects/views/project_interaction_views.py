"""
Views for project interaction models.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.projects.models.project_interaction import (
    ProjectInterest, ProjectFavorite, ProjectQuestion, ProjectQuestionAnswer, ProjectReport
)
from apps.projects.serializers import (
    ProjectInterestSerializer, ProjectInterestCreateSerializer, ProjectInterestUpdateSerializer,
    ProjectFavoriteSerializer, ProjectQuestionSerializer, ProjectQuestionCreateSerializer,
    ProjectQuestionAnswerSerializer, ProjectQuestionAnswerCreateSerializer,
    ProjectReportSerializer, ProjectReportCreateSerializer
)
from apps.projects.services.project_service import ProjectService
from apps.projects.services.project_interaction_service import ProjectInteractionService


class ProjectInterestViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectInterest."""
    queryset = ProjectInterest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'is_anonymous']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return interests for a specific project or user.
        Project creators can see all interests for their projects.
        Users can see their own interests.
        """
        user = self.request.user
        project_id = self.kwargs.get('project_pk')
        
        # Intérêts pour un projet spécifique
        if project_id:
            try:
                project = ProjectService.get_project_by_id(project_id, user)
                
                # Si l'utilisateur est le créateur du projet, montrer tous les intérêts
                if project.creator == user:
                    return ProjectInterest.objects.filter(project=project)
                    
                # Sinon, montrer seulement les intérêts de l'utilisateur
                return ProjectInterest.objects.filter(project=project, user=user)
            except ResourceNotFoundError:
                return ProjectInterest.objects.none()
                
        # Sans projet spécifié, montrer tous les intérêts de l'utilisateur
        return ProjectInterest.objects.filter(user=user)

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return ProjectInterestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectInterestUpdateSerializer
        return ProjectInterestSerializer

    def create(self, request, *args, **kwargs):
        """
        Create an interest for a project.
        """
        project_id = request.data.get('project')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            interest = ProjectInteractionService.create_project_interest(
                user=request.user,
                project_id=project_id,
                data=serializer.validated_data
            )
            return Response(
                ProjectInterestSerializer(interest).data,
                status=status.HTTP_201_CREATED
            )
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, *args, **kwargs):
        """
        Update an interest status (mainly for project owners).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Seul le créateur du projet peut changer le statut
        if request.user != instance.project.creator:
            return Response(
                {'detail': _('Seul le créateur du projet peut mettre à jour le statut.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            interest = ProjectInteractionService.update_project_interest_status(
                interest_id=instance.id,
                user=request.user,
                status=serializer.validated_data['status']
            )
            return Response(ProjectInterestSerializer(interest).data)
        except PermissionDeniedError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete an interest (only if user is the creator of the interest).
        """
        instance = self.get_object()
        
        if request.user != instance.user and request.user != instance.project.creator:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer cet intérêt.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectFavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectFavorite."""
    queryset = ProjectFavorite.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        This view should return only the user's favorites.
        """
        return ProjectFavorite.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """
        Return the serializer for this viewset.
        """
        return ProjectFavoriteSerializer

    def create(self, request, *args, **kwargs):
        """
        Add a project to favorites.
        """
        project_id = request.data.get('project')
        notes = request.data.get('notes')

        try:
            favorite = ProjectInteractionService.add_project_to_favorites(
                user=request.user,
                project_id=project_id,
                notes=notes
            )
            return Response(
                ProjectFavoriteSerializer(favorite).data,
                status=status.HTTP_201_CREATED
            )
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        """
        Retirer un projet des favoris.
        """
        project_id = request.data.get('project')

        if not project_id:
            return Response(
                {'detail': 'Le champ project est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ProjectInteractionService.remove_project_from_favorites(
                user=request.user,
                project_id=project_id
            )
            return Response(
                {'detail': 'Favori supprimé'},
                status=status.HTTP_204_NO_CONTENT
            )
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Vérifier si un projet est en favoris.
        """
        project_id = request.query_params.get('project')

        if not project_id:
            return Response(
                {'detail': 'Le paramètre project est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_favorited = ProjectFavorite.objects.filter(
            user=request.user,
            project_id=project_id
        ).exists()

        return Response({'is_favorited': is_favorited})

    def destroy(self, request, *args, **kwargs):
        """
        Remove a project from favorites.
        """
        instance = self.get_object()

        if request.user != instance.user:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer ce favori.')},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectQuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectQuestion."""
    queryset = ProjectQuestion.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'is_public', 'is_answered']
    search_fields = ['question']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return questions for a specific project.
        """
        project_id = self.kwargs.get('project_pk')
        user = self.request.user
        include_non_public = False
        
        if project_id:
            try:
                project = ProjectService.get_project_by_id(project_id, user)
                
                # Si l'utilisateur est le créateur du projet, inclure aussi les questions non publiques
                if project.creator == user:
                    include_non_public = True
                    
                return ProjectInteractionService.get_project_questions(
                    project_id=project_id,
                    user=user,
                    include_non_public=include_non_public
                )
            except ResourceNotFoundError:
                return ProjectQuestion.objects.none()
                
        # Si l'utilisateur veut voir toutes les questions qu'il a posées
        return ProjectQuestion.objects.filter(user=user)

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return ProjectQuestionCreateSerializer
        return ProjectQuestionSerializer

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
        Create a question for a project.
        """
        project_id = request.data.get('project')
        question_text = request.data.get('question')
        is_public = request.data.get('is_public', True)
        
        try:
            question = ProjectInteractionService.create_project_question(
                user=request.user,
                project_id=project_id,
                question_text=question_text,
                is_public=is_public
            )
            return Response(
                ProjectQuestionSerializer(question).data,
                status=status.HTTP_201_CREATED
            )
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete a question.
        """
        instance = self.get_object()
        
        if request.user != instance.user and request.user != instance.project.creator:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer cette question.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectQuestionAnswerViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectQuestionAnswer."""
    queryset = ProjectQuestionAnswer.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['question']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return answers for a specific question.
        """
        question_id = self.kwargs.get('question_pk')
        if question_id:
            return ProjectQuestionAnswer.objects.filter(question_id=question_id)
        return ProjectQuestionAnswer.objects.none()

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return ProjectQuestionAnswerCreateSerializer
        return ProjectQuestionAnswerSerializer

    def create(self, request, *args, **kwargs):
        """
        Create an answer for a question.
        """
        question_id = request.data.get('question')
        answer_text = request.data.get('answer')
        
        try:
            answer = ProjectInteractionService.answer_project_question(
                user=request.user,
                question_id=question_id,
                answer_text=answer_text
            )
            return Response(
                ProjectQuestionAnswerSerializer(answer).data,
                status=status.HTTP_201_CREATED
            )
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        
    def update(self, request, *args, **kwargs):
        """
        Update an answer.
        """
        instance = self.get_object()
        
        if request.user != instance.answered_by:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à modifier cette réponse.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        answer = serializer.save()
        
        return Response(ProjectQuestionAnswerSerializer(answer).data)
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete an answer.
        """
        instance = self.get_object()
        
        if request.user != instance.answered_by and request.user != instance.question.project.creator:
            return Response(
                {'detail': _('Vous n\'êtes pas autorisé à supprimer cette réponse.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 


class ProjectReportViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectReport."""
    queryset = ProjectReport.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'reason', 'is_resolved']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        project_id = self.kwargs.get('project_pk')

        if project_id:
            try:
                return ProjectInteractionService.get_project_reports(project_id=project_id, user=user)
            except PermissionDeniedError:
                return ProjectReport.objects.none()
        # Sinon, retourner les signalements faits par l'utilisateur
        return ProjectReport.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectReportCreateSerializer
        return ProjectReportSerializer

    def create(self, request, *args, **kwargs):
        project_id = request.data.get('project')
        reason = request.data.get('reason')
        description = request.data.get('description', '')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            report = ProjectInteractionService.create_project_report(
                user=request.user,
                project_id=project_id,
                reason=reason,
                description=description
            )
            return Response(ProjectReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except (ValidationError, ResourceNotFoundError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Un utilisateur peut retirer son propre report ou un admin peut le supprimer
        if request.user != instance.user and not request.user.is_staff:
            return Response({'detail': _('Vous n\'êtes pas autorisé à supprimer ce signalement.')}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 