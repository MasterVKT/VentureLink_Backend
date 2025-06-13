"""
Views for project models.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db import models

from apps.core.permissions import IsOwnerOrReadOnly, IsAdminUser
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.projects.models.project import Project, ProjectCategory, ProjectTag
from apps.projects.permissions import IsPublishedProjectOrCreator
from apps.projects.serializers import (
    ProjectCategorySerializer, ProjectTagSerializer,
    ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, ProjectUpdateSerializer,
    ProjectPublishSerializer
)
from apps.projects.services.project_service import ProjectService


class ProjectCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectCategory."""
    queryset = ProjectCategory.objects.filter(is_active=True)
    serializer_class = ProjectCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name_fr', 'name_en']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ProjectTagViewSet(viewsets.ModelViewSet):
    """ViewSet for ProjectTag."""
    queryset = ProjectTag.objects.filter(is_active=True)
    serializer_class = ProjectTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name_fr', 'name_en']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project."""
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsPublishedProjectOrCreator]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'category', 'stage', 'is_premium', 'is_featured', 'status',
        'location_country', 'tags', 'funding_min', 'funding_max'
    ]
    search_fields = ['title', 'short_description', 'full_description', 
                     'creator__first_name', 'creator__last_name', 
                     'tags__name_fr', 'tags__name_en']
    ordering_fields = ['created_at', 'published_at', 'views_count', 'interests_count', 'favorites_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        This view should return a list of all projects for the authenticated user
        and all published projects for other users. Includes caching for performance.
        """
        # Créer une clé de cache basée sur l'utilisateur et les filtres
        user_id = self.request.user.id if self.request.user.is_authenticated else 'anonymous'
        filters_key = str(sorted(self.request.query_params.items()))
        cache_key = f"projects_list_{user_id}_{hash(filters_key)}"
        
        # Essayer de récupérer depuis le cache
        cached_projects = cache.get(cache_key)
        if cached_projects is not None:
            return cached_projects
        
        # Si pas en cache, récupérer depuis la DB avec optimisations
        queryset = Project.objects.select_related(
            'creator', 'category'
        ).prefetch_related(
            'tags', 'media', 'favorites', 'interests'
        )
        
        # Appliquer les filtres via le service
        filtered_queryset = ProjectService.get_projects(
            user=self.request.user,
            filters=self.request.query_params.dict(),
            category=self.request.query_params.get('category'),
            search=self.request.query_params.get('search')
        )
        
        # Mettre en cache pour 15 minutes
        cache.set(cache_key, filtered_queryset, 900)
        
        return filtered_queryset

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ProjectUpdateSerializer
        elif self.action == 'publish':
            return ProjectPublishSerializer
        return ProjectDetailSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve', 'trending', 'featured', 'filter_options']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'publish']:
            from apps.projects.permissions import IsProjectCreator
            permission_classes = [permissions.IsAuthenticated, IsProjectCreator]
        elif self.action in ['related']:
            permission_classes = [IsPublishedProjectOrCreator]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a project and increment its view count.
        """
        try:
            project = ProjectService.get_project_by_id(
                project_id=kwargs['pk'],
                user=request.user if request.user.is_authenticated else None
            )
            
            # Increment view count only for public projects
            if not project.is_draft:
                ProjectService.increment_view_count(project.id)
                
            serializer = self.get_serializer(project)
            return Response(serializer.data)
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        Create a project.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            project = ProjectService.create_project(
                user=request.user,
                data=serializer.validated_data
            )
            return Response(ProjectDetailSerializer(project).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update a project.
        """
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            project = ProjectService.update_project(
                project_id=kwargs['pk'],
                user=request.user,
                data=serializer.validated_data
            )
            return Response(ProjectDetailSerializer(project).data)
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDeniedError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a project.
        """
        try:
            ProjectService.delete_project(
                project_id=kwargs['pk'],
                user=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDeniedError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        Publish a project (change is_draft to False).
        """
        try:
            project = ProjectService.publish_project(
                project_id=pk,
                user=request.user
            )
            return Response(ProjectDetailSerializer(project).data)
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='my-projects')
    def my_projects(self, request):
        """
        Return user's projects.
        """
        queryset = Project.objects.filter(creator=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='trending')
    def trending(self, request):
        """
        Return trending projects.
        """
        days = request.query_params.get('days', 7)
        limit = request.query_params.get('limit', 10)
        
        try:
            days = int(days)
            limit = int(limit)
        except ValueError:
            days = 7
            limit = 10
        
        projects = ProjectService.get_trending_projects(limit=limit, days=days)
        serializer = ProjectListSerializer(projects, many=True, context={'request': request})
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        """
        Return featured projects.
        """
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        projects = ProjectService.get_featured_projects(limit=limit)
        serializer = ProjectListSerializer(projects, many=True, context={'request': request})
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='related')
    def related(self, request, pk=None):
        """
        Return projects related to this project.
        """
        try:
            project = ProjectService.get_project_by_id(pk, request.user)
            
            # Vérifier si l'utilisateur a le droit de voir ce projet
            if project.is_draft and (not request.user or request.user != project.creator):
                return Response(
                    {'detail': 'Projet non trouvé.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            limit = request.query_params.get('limit', 5)
            
            try:
                limit = int(limit)
            except ValueError:
                limit = 5
            
            related_projects = ProjectService.get_related_projects(project, limit=limit)
            serializer = ProjectListSerializer(related_projects, many=True, context={'request': request})
            
            return Response(serializer.data)
            
        except ResourceNotFoundError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Return available filter options.
        """
        categories = ProjectCategory.objects.filter(is_active=True)
        tags = ProjectTag.objects.filter(is_active=True)
        
        categories_data = [{'id': cat.id, 'name': cat.name_fr} for cat in categories]
        tags_data = [{'id': tag.id, 'name': tag.name_fr} for tag in tags]
        
        # Stages disponibles
        stages_data = [
            {'value': 'idea', 'name': 'Idée'},
            {'value': 'prototype', 'name': 'Prototype'},
            {'value': 'mvp', 'name': 'MVP'},
            {'value': 'growth', 'name': 'Croissance'},
            {'value': 'scale', 'name': 'Expansion'},
        ]
        
        # Locations les plus populaires
        locations = Project.objects.values('location_country', 'location_city').distinct()[:20]
        locations_data = [
            {
                'country': loc['location_country'],
                'city': loc['location_city']
            } for loc in locations if loc['location_country']
        ]
        
        return Response({
            'categories': categories_data,
            'tags': tags_data,
            'stages': stages_data,
            'locations': locations_data,
        })

    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        """
        Ajouter/retirer un projet des favoris.
        """
        try:
            project = self.get_object()
            user = request.user
            
            # Vérifier si déjà en favoris
            if project.favorites.filter(id=user.id).exists():
                project.favorites.remove(user)
                is_favorite = False
                message = "Projet retiré des favoris"
            else:
                project.favorites.add(user)
                is_favorite = True
                message = "Projet ajouté aux favoris"
            
            return Response({
                'is_favorite': is_favorite,
                'message': message,
                'favorites_count': project.favorites.count()
            })
            
        except Exception as e:
            return Response(
                {'error': 'Erreur lors de la mise à jour des favoris'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='toggle-interest')
    def toggle_interest(self, request, pk=None):
        """
        Exprimer/retirer son intérêt pour un projet.
        """
        try:
            project = self.get_object()
            user = request.user
            
            # Vérifier si déjà intéressé
            if project.interests.filter(id=user.id).exists():
                project.interests.remove(user)
                is_interested = False
                message = "Intérêt retiré"
            else:
                project.interests.add(user)
                is_interested = True
                message = "Intérêt exprimé"
                
                # Créer notification pour le créateur du projet
                from apps.notifications.services import NotificationService
                NotificationService.create_notification(
                    recipient=project.creator,
                    title="Nouvel intérêt pour votre projet",
                    content=f"{user.get_full_name()} s'intéresse à votre projet '{project.title}'",
                    category='project',
                    related_object=project
                )
            
            return Response({
                'is_interested': is_interested,
                'message': message,
                'interests_count': project.interests.count()
            })
            
        except Exception as e:
            return Response(
                {'error': 'Erreur lors de la mise à jour de l\'intérêt'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        """
        Retourner les projets favoris de l'utilisateur.
        """
        queryset = Project.objects.filter(
            favorites=request.user
        ).select_related('creator', 'category').prefetch_related('tags', 'media')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='interests')
    def interests(self, request):
        """
        Retourner les projets pour lesquels l'utilisateur a exprimé un intérêt.
        """
        queryset = Project.objects.filter(
            interests=request.user
        ).select_related('creator', 'category').prefetch_related('tags', 'media')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class ProjectSearchView(viewsets.GenericViewSet):
    """
    View pour recherche avancée de projets.
    """
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """
        Recherche avancée avec filtres multiples.
        """
        search_query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        location_country = request.query_params.get('location_country')
        location_city = request.query_params.get('location_city')
        funding_min = request.query_params.get('funding_min')
        funding_max = request.query_params.get('funding_max')
        stage = request.query_params.get('stage')
        tags = request.query_params.getlist('tags')
        
        # Cache key pour la recherche
        cache_key = f"search_{hash(str(request.query_params.dict()))}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            return Response(cached_results)
        
        # Base queryset
        queryset = Project.objects.filter(
            status='published'
        ).select_related(
            'creator', 'category'
        ).prefetch_related('tags', 'media')
        
        # Filtres de recherche
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(short_description__icontains=search_query) |
                models.Q(full_description__icontains=search_query) |
                models.Q(tags__name_fr__icontains=search_query) |
                models.Q(tags__name_en__icontains=search_query)
            ).distinct()
        
        if category:
            queryset = queryset.filter(category__id=category)
        
        if location_country:
            queryset = queryset.filter(location_country__icontains=location_country)
            
        if location_city:
            queryset = queryset.filter(location_city__icontains=location_city)
        
        if funding_min:
            try:
                queryset = queryset.filter(funding_min__gte=float(funding_min))
            except ValueError:
                pass
                
        if funding_max:
            try:
                queryset = queryset.filter(funding_max__lte=float(funding_max))
            except ValueError:
                pass
        
        if stage:
            queryset = queryset.filter(stage=stage)
        
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True, context={'request': request})
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
            response_data = serializer.data
        
        # Cache pour 10 minutes
        cache.set(cache_key, response_data, 600)
        
        return Response(response_data)


class TrendingProjectsView(viewsets.GenericViewSet):
    """
    View pour les projets tendance.
    """
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """
        Retourne les projets les plus populaires récemment.
        """
        days = request.query_params.get('days', 7)
        limit = request.query_params.get('limit', 20)
        
        try:
            days = int(days)
            limit = int(limit)
        except ValueError:
            days = 7
            limit = 20
        
        cache_key = f"trending_projects_{days}_{limit}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            return Response(cached_results)
        
        # Calcul des projets tendance basé sur vues, intérêts et favoris récents
        from django.utils import timezone
        from datetime import timedelta
        
        recent_date = timezone.now() - timedelta(days=days)
        
        queryset = Project.objects.filter(
            status='published',
            published_at__gte=recent_date
        ).select_related(
            'creator', 'category'
        ).prefetch_related('tags', 'media').annotate(
            popularity_score=models.F('views_count') + 
                           models.F('interests_count') * 2 + 
                           models.F('favorites_count') * 3
        ).order_by('-popularity_score')[:limit]
        
        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        
        # Cache pour 30 minutes
        cache.set(cache_key, serializer.data, 1800)
        
        return Response(serializer.data) 