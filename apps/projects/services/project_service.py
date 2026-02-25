"""
Service layer for project operations.
"""
from django.db.models import Q, F
from django.utils import timezone
from decimal import Decimal
from django.conf import settings

from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.projects.models.project import Project, ProjectCategory, ProjectTag
from apps.core.services.currency_service import CurrencyService


class ProjectService:
    """
    Service for project operations.
    """
    
    @staticmethod
    def get_projects(user=None, filters=None, category=None, search=None, only_active=True, ordering='-created_at'):
        """
        Get projects based on various filters.
        
        Args:
            user (User, optional): Current user
            filters (dict): Dictionary of filters to apply
            category (str): Category filter
            search (str): Search term
            only_active (bool): Filter only active projects
            ordering (str): Field to order by
            
        Returns:
            QuerySet: Projects matching the criteria
        """
        filters = filters or {}
        queryset = Project.objects.all()
        
        # Filter by draft status - non-draft (published) projects are visible to all
        if user and user.is_authenticated:
            # Include user's own draft projects plus all published projects
            queryset = queryset.filter(
                Q(is_draft=False) | 
                Q(is_draft=True, creator=user)
            )
        else:
            # Only show published projects to non-authenticated users
            queryset = queryset.filter(is_draft=False)
        
        # Filter by active status
        if only_active:
            queryset = queryset.filter(status='ACTIVE')
        
        # Apply category filter
        if category:
            import uuid
            try:
                uuid.UUID(str(category))
                # C'est un UUID valide → filtre par ID
                queryset = queryset.filter(category__id=category)
            except ValueError:
                # C'est un nom → filtre par nom
                queryset = queryset.filter(
                    Q(category__name_fr__icontains=category) |
                    Q(category__name_en__icontains=category)
                )
        
        # Apply tag filter
        if 'tags' in filters:
            tags = filters.get('tags')
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            if tags:
                queryset = queryset.filter(tags__id__in=tags).distinct()
        
        # Apply location filters
        if 'location_country' in filters:
            queryset = queryset.filter(location_country__iexact=filters['location_country'])
        
        if 'location_city' in filters:
            queryset = queryset.filter(location_city__icontains=filters['location_city'])
        
        # Apply funding range filters
        funding_min = filters.get('funding_min')
        funding_max = filters.get('funding_max')
        funding_currency = filters.get('funding_currency', settings.DEFAULT_CURRENCY)
        
        if funding_min or funding_max:
            # Convertir les montants dans la devise standard si nécessaire
            if funding_currency.upper() != settings.DEFAULT_CURRENCY:
                currency_service = CurrencyService()
                if funding_min:
                    funding_min = currency_service.convert_currency(
                        amount=Decimal(funding_min),
                        from_currency=funding_currency,
                        to_currency=settings.DEFAULT_CURRENCY
                    )
                if funding_max:
                    funding_max = currency_service.convert_currency(
                        amount=Decimal(funding_max),
                        from_currency=funding_currency,
                        to_currency=settings.DEFAULT_CURRENCY
                    )
            
            # Appliquer les filtres de financement
            if funding_min:
                queryset = queryset.filter(funding_min__gte=funding_min)
            if funding_max:
                queryset = queryset.filter(funding_max__lte=funding_max)
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_description__icontains=search) |
                Q(full_description__icontains=search) |
                Q(creator__first_name__icontains=search) |
                Q(creator__last_name__icontains=search) |
                Q(tags__name_fr__icontains=search) |
                Q(tags__name_en__icontains=search)
            ).distinct()
        
        # Apply stage filter
        if 'stage' in filters:
            stages = filters.get('stage')
            if isinstance(stages, str):
                stages = [stage.strip() for stage in stages.split(',')]
            if stages:
                queryset = queryset.filter(stage__in=stages)
        
        # Apply other custom filters
        standard_filters = [
            'creator', 'is_premium', 'is_featured', 'status'
        ]
        
        for key in standard_filters:
            if key in filters:
                queryset = queryset.filter(**{key: filters[key]})
        
        # Apply ordering
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_project_by_id(project_id, user=None):
        """
        Get a project by its ID.
        
        Args:
            project_id (uuid): Project ID
            user (User, optional): Current user
            
        Returns:
            Project: The project
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist or user can't access it
        """
        try:
            project = Project.objects.get(id=project_id)
            
            # Check if user can access this project
            if project.is_draft and (not user or not user.is_authenticated or user != project.creator):
                raise ResourceNotFoundError("Projet non trouvé.")
                
            return project
        except Project.DoesNotExist:
            raise ResourceNotFoundError("Projet non trouvé.")
    
    @staticmethod
    def create_project(user, data):
        """
        Create a new project.
        
        Args:
            user (User): The creator
            data (dict): Project data
            
        Returns:
            Project: The created project
        """
        project = Project.objects.create(
            creator=user,
            **data
        )
        
        return project
    
    @staticmethod
    def update_project(project_id, user, data):
        """
        Update a project.
        
        Args:
            project_id (uuid): Project ID
            user (User): Current user
            data (dict): Updated data
            
        Returns:
            Project: The updated project
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            PermissionDeniedError: If the user is not the creator
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        if project.creator != user:
            raise PermissionDeniedError("Vous n'êtes pas autorisé à modifier ce projet.")
        
        for key, value in data.items():
            if key == 'tags':
                project.tags.set(value)
            else:
                setattr(project, key, value)
        
        project.save()
        return project
    
    @staticmethod
    def delete_project(project_id, user):
        """
        Delete a project.
        
        Args:
            project_id (uuid): Project ID
            user (User): Current user
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            PermissionDeniedError: If the user is not the creator
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        if project.creator != user:
            raise PermissionDeniedError("Vous n'êtes pas autorisé à supprimer ce projet.")
        
        project.delete()
    
    @staticmethod
    def publish_project(project_id, user):
        """
        Publish a project (mark as non-draft).
        
        Args:
            project_id (uuid): Project ID
            user (User): Current user
            
        Returns:
            Project: The published project
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            PermissionDeniedError: If the user is not the creator
            ValidationError: If the project is invalid
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        if project.creator != user:
            raise PermissionDeniedError("Vous n'êtes pas autorisé à publier ce projet.")
        
        if not project.is_draft:
            raise ValidationError("Ce projet est déjà publié.")
        
        # Validation pour la publication
        if not project.title or not project.short_description or not project.full_description:
            raise ValidationError("Le projet doit avoir un titre, une description courte et une description complète.")
        
        if not project.category:
            raise ValidationError("Le projet doit avoir une catégorie.")
            
        # Mettre à jour le statut du projet
        project.is_draft = False
        project.published_at = timezone.now()
        project.save()
        
        return project
        
    @staticmethod
    def increment_view_count(project_id):
        """
        Increment the view count of a project.
        
        Args:
            project_id (uuid): Project ID
        """
        Project.objects.filter(id=project_id).update(views_count=F('views_count') + 1)
    
    @staticmethod
    def get_trending_projects(limit=10, days=7):
        """
        Get trending projects based on views and interests from the last N days.
        
        Args:
            limit (int): Number of projects to return
            days (int): Number of days to consider
            
        Returns:
            QuerySet: Trending projects
        """
        date_threshold = timezone.now() - timezone.timedelta(days=days)
        
        return Project.objects.filter(
            is_draft=False,
            status='ACTIVE',
            published_at__gte=date_threshold
        ).order_by('-views_count', '-interests_count', '-favorites_count')[:limit]
    
    @staticmethod
    def get_featured_projects(limit=10):
        """
        Get featured projects.
        
        Args:
            limit (int): Number of projects to return
            
        Returns:
            QuerySet: Featured projects
        """
        return Project.objects.filter(
            is_draft=False,
            status='ACTIVE',
            is_featured=True
        ).order_by('-published_at')[:limit]
    
    @staticmethod
    def get_related_projects(project, limit=5):
        """
        Get projects related to a given project based on category and tags.
        
        Args:
            project (Project): The reference project
            limit (int): Number of projects to return
            
        Returns:
            QuerySet: Related projects
        """
        return Project.objects.filter(
            is_draft=False,
            status='ACTIVE',
            category=project.category
        ).exclude(id=project.id).order_by('-published_at')[:limit] 