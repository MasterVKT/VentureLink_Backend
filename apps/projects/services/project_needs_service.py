"""
Service for managing project needs and skills.
"""
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from apps.projects.models import Project, ProjectNeeds, ProjectSkillsNeeded


class ProjectNeedsService:
    """Service for managing project needs."""

    @staticmethod
    def get_project_needs(project_id, resource_type=None, is_satisfied=None):
        """
        Get needs for a project with optional filtering.
        
        Args:
            project_id: The project ID
            resource_type: Optional resource type filter
            is_satisfied: Optional satisfaction status filter
            
        Returns:
            QuerySet of ProjectNeeds objects
        """
        needs = ProjectNeeds.objects.filter(project_id=project_id)
        
        if resource_type:
            needs = needs.filter(resource_type=resource_type)
            
        if is_satisfied is not None:
            needs = needs.filter(is_satisfied=is_satisfied)
            
        return needs.order_by('is_satisfied', 'is_critical', '-created_at')

    @staticmethod
    def get_need_detail(need_id, project_id=None):
        """
        Get a specific project need.
        
        Args:
            need_id: The need ID
            project_id: Optional project ID to validate ownership
            
        Returns:
            ProjectNeeds object
            
        Raises:
            ProjectNeeds.DoesNotExist: If need not found
        """
        if project_id:
            return ProjectNeeds.objects.get(id=need_id, project_id=project_id)
        return ProjectNeeds.objects.get(id=need_id)

    @staticmethod
    def create_need(project_id, creator, resource_type, title, description, amount=None, 
                    currency='EUR', is_critical=False, deadline=None):
        """
        Create a new need for a project.
        
        Args:
            project_id: The project ID
            creator: User creating the need
            resource_type: Type of resource needed
            title: Title of the need
            description: Description of the need
            amount: Optional financial amount
            currency: Currency code for amount
            is_critical: Whether this need is critical
            deadline: Optional deadline date
            
        Returns:
            Created ProjectNeeds object
            
        Raises:
            PermissionDenied: If user is not the project creator
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != creator:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à ajouter des besoins à ce projet"))
        
        # Create the need
        need = ProjectNeeds.objects.create(
            project=project,
            resource_type=resource_type,
            title=title,
            description=description,
            amount=amount,
            amount_currency=currency if amount else project.funding_currency,
            is_critical=is_critical,
            deadline=deadline,
            is_satisfied=False
        )
        
        return need

    @staticmethod
    def update_need(need_id, project_id, user, data):
        """
        Update a project need.
        
        Args:
            need_id: The need ID
            project_id: The project ID
            user: User performing the update
            data: Dictionary with fields to update
            
        Returns:
            Updated ProjectNeeds object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectNeeds.DoesNotExist: If need not found
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier les besoins de ce projet"))
        
        # Get the need
        need = ProjectNeeds.objects.get(id=need_id, project=project)
        
        # Update fields
        for field, value in data.items():
            if hasattr(need, field) and field != 'project':
                setattr(need, field, value)
        
        # Handle currency updates
        if 'amount' in data and 'amount_currency' not in data:
            need.amount_currency = project.funding_currency
            
        need.save()
        return need

    @staticmethod
    def delete_need(need_id, project_id, user):
        """
        Delete a project need.
        
        Args:
            need_id: The need ID
            project_id: The project ID
            user: User performing the deletion
            
        Returns:
            bool: True if successful
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectNeeds.DoesNotExist: If need not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à supprimer les besoins de ce projet"))
        
        # Get the need and delete
        need = ProjectNeeds.objects.get(id=need_id, project=project)
        need.delete()
        
        return True

    @staticmethod
    def mark_as_satisfied(need_id, project_id, user, satisfied=True):
        """
        Mark a project need as satisfied or unsatisfied.
        
        Args:
            need_id: The need ID
            project_id: The project ID
            user: User performing the action
            satisfied: Whether to mark as satisfied (True) or unsatisfied (False)
            
        Returns:
            Updated ProjectNeeds object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectNeeds.DoesNotExist: If need not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier les besoins de ce projet"))
        
        # Get the need
        need = ProjectNeeds.objects.get(id=need_id, project=project)
        
        # Update satisfaction status
        need.is_satisfied = satisfied
        need.save(update_fields=['is_satisfied', 'updated_at'])
        
        return need


class ProjectSkillsService:
    """Service for managing project skills needed."""

    @staticmethod
    def get_project_skills(project_id, priority=None, is_satisfied=None):
        """
        Get skills needed for a project with optional filtering.
        
        Args:
            project_id: The project ID
            priority: Optional priority filter
            is_satisfied: Optional satisfaction status filter
            
        Returns:
            QuerySet of ProjectSkillsNeeded objects
        """
        skills = ProjectSkillsNeeded.objects.filter(project_id=project_id)
        
        if priority:
            skills = skills.filter(priority=priority)
            
        if is_satisfied is not None:
            skills = skills.filter(is_satisfied=is_satisfied)
            
        return skills.order_by('is_satisfied', '-priority', 'name')

    @staticmethod
    def get_skill_detail(skill_id, project_id=None):
        """
        Get a specific project skill.
        
        Args:
            skill_id: The skill ID
            project_id: Optional project ID to validate ownership
            
        Returns:
            ProjectSkillsNeeded object
            
        Raises:
            ProjectSkillsNeeded.DoesNotExist: If skill not found
        """
        if project_id:
            return ProjectSkillsNeeded.objects.get(id=skill_id, project_id=project_id)
        return ProjectSkillsNeeded.objects.get(id=skill_id)

    @staticmethod
    def create_skill(project_id, creator, name, description=None, priority=ProjectSkillsNeeded.PRIORITY_MEDIUM, required_level=3):
        """
        Create a new skill needed for a project.
        
        Args:
            project_id: The project ID
            creator: User creating the skill
            name: Name of the skill
            description: Optional description
            priority: Priority level
            required_level: Required skill level (1-5)
            
        Returns:
            Created ProjectSkillsNeeded object
            
        Raises:
            PermissionDenied: If user is not the project creator
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != creator:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à ajouter des compétences à ce projet"))
        
        # Create the skill
        skill = ProjectSkillsNeeded.objects.create(
            project=project,
            name=name,
            description=description,
            priority=priority,
            required_level=required_level,
            is_satisfied=False
        )
        
        return skill

    @staticmethod
    def update_skill(skill_id, project_id, user, data):
        """
        Update a project skill.
        
        Args:
            skill_id: The skill ID
            project_id: The project ID
            user: User performing the update
            data: Dictionary with fields to update
            
        Returns:
            Updated ProjectSkillsNeeded object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectSkillsNeeded.DoesNotExist: If skill not found
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier les compétences requises de ce projet"))
        
        # Get the skill
        skill = ProjectSkillsNeeded.objects.get(id=skill_id, project=project)
        
        # Update fields
        for field, value in data.items():
            if hasattr(skill, field) and field != 'project':
                setattr(skill, field, value)
        
        skill.save()
        return skill

    @staticmethod
    def delete_skill(skill_id, project_id, user):
        """
        Delete a project skill.
        
        Args:
            skill_id: The skill ID
            project_id: The project ID
            user: User performing the deletion
            
        Returns:
            bool: True if successful
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectSkillsNeeded.DoesNotExist: If skill not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à supprimer les compétences requises de ce projet"))
        
        # Get the skill and delete
        skill = ProjectSkillsNeeded.objects.get(id=skill_id, project=project)
        skill.delete()
        
        return True

    @staticmethod
    def mark_as_satisfied(skill_id, project_id, user, satisfied=True):
        """
        Mark a project skill as satisfied or unsatisfied.
        
        Args:
            skill_id: The skill ID
            project_id: The project ID
            user: User performing the action
            satisfied: Whether to mark as satisfied (True) or unsatisfied (False)
            
        Returns:
            Updated ProjectSkillsNeeded object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectSkillsNeeded.DoesNotExist: If skill not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier les compétences requises de ce projet"))
        
        # Get the skill
        skill = ProjectSkillsNeeded.objects.get(id=skill_id, project=project)
        
        # Update satisfaction status
        skill.is_satisfied = satisfied
        skill.save(update_fields=['is_satisfied', 'updated_at'])
        
        return skill 