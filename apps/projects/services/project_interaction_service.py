"""
Service layer for project interactions.
"""
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.projects.models.project_interaction import (
    ProjectInterest, ProjectFavorite, 
    ProjectQuestion, ProjectQuestionAnswer
)
from apps.projects.services.project_service import ProjectService


class ProjectInteractionService:
    """
    Service for project interaction operations.
    """
    
    @staticmethod
    def get_project_interests(project_id, user=None):
        """
        Get interests for a project.
        
        Args:
            project_id (uuid): Project ID
            user (User, optional): Current user
            
        Returns:
            QuerySet: Project interests
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            PermissionDeniedError: If the user is not the creator
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        # Check if user is the project creator
        if not user or user != project.creator:
            raise PermissionDeniedError("Seul le créateur du projet peut voir les marques d'intérêt.")
        
        return ProjectInterest.objects.filter(project=project)
    
    @staticmethod
    def create_project_interest(user, project_id, data):
        """
        Create a new project interest.
        
        Args:
            user (User): Current user
            project_id (uuid): Project ID
            data (dict): Interest data
            
        Returns:
            ProjectInterest: The created interest
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            ValidationError: If the user already expressed interest
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        # Check if user already expressed interest
        if ProjectInterest.objects.filter(user=user, project=project).exists():
            raise ValidationError("Vous avez déjà exprimé un intérêt pour ce projet.")
        
        # Check if project is not draft
        if project.is_draft:
            raise ValidationError("Vous ne pouvez pas exprimer d'intérêt pour un projet en brouillon.")
        
        interest = ProjectInterest.objects.create(
            user=user,
            project=project,
            **data
        )
        
        return interest
    
    @staticmethod
    def update_project_interest_status(interest_id, user, status):
        """
        Update the status of a project interest.
        
        Args:
            interest_id (uuid): Interest ID
            user (User): Current user
            status (str): New status
            
        Returns:
            ProjectInterest: The updated interest
            
        Raises:
            ResourceNotFoundError: If the interest doesn't exist
            PermissionDeniedError: If the user is not the project creator
        """
        try:
            interest = ProjectInterest.objects.get(id=interest_id)
        except ProjectInterest.DoesNotExist:
            raise ResourceNotFoundError("Intérêt non trouvé.")
        
        # Check if user is the project creator
        if user != interest.project.creator:
            raise PermissionDeniedError("Seul le créateur du projet peut mettre à jour le statut.")
        
        interest.status = status
        interest.save()
        
        return interest
    
    @staticmethod
    def get_user_project_favorites(user):
        """
        Get all favorites for a user.
        
        Args:
            user (User): Current user
            
        Returns:
            QuerySet: User favorites
        """
        return ProjectFavorite.objects.filter(user=user)
    
    @staticmethod
    def add_project_to_favorites(user, project_id, notes=None):
        """
        Add a project to user's favorites.
        
        Args:
            user (User): Current user
            project_id (uuid): Project ID
            notes (str, optional): User notes
            
        Returns:
            ProjectFavorite: The created favorite
            
        Raises:
            ResourceNotFoundError: If the project doesn't exist
            ValidationError: If already in favorites
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        # Check if already in favorites
        if ProjectFavorite.objects.filter(user=user, project=project).exists():
            raise ValidationError("Ce projet est déjà dans vos favoris.")
        
        favorite = ProjectFavorite.objects.create(
            user=user,
            project=project,
            notes=notes
        )
        
        return favorite
    
    @staticmethod
    def remove_project_from_favorites(user, project_id):
        """
        Remove a project from user's favorites.
        
        Args:
            user (User): Current user
            project_id (uuid): Project ID
            
        Raises:
            ResourceNotFoundError: If the favorite doesn't exist
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        try:
            favorite = ProjectFavorite.objects.get(user=user, project=project)
            favorite.delete()
        except ProjectFavorite.DoesNotExist:
            raise ResourceNotFoundError("Ce projet n'est pas dans vos favoris.")
    
    @staticmethod
    def get_project_questions(project_id, user=None, include_non_public=False):
        """
        Get questions for a project.
        
        Args:
            project_id (uuid): Project ID
            user (User, optional): Current user
            include_non_public (bool): Whether to include non-public questions
            
        Returns:
            QuerySet: Project questions
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        questions = ProjectQuestion.objects.filter(project=project)
        
        # If not the project creator, filter out non-public questions
        if not include_non_public or not user or user != project.creator:
            questions = questions.filter(is_public=True)
        
        return questions
    
    @staticmethod
    def create_project_question(user, project_id, question_text, is_public=True):
        """
        Create a new question for a project.
        
        Args:
            user (User): Current user
            project_id (uuid): Project ID
            question_text (str): Question text
            is_public (bool): Whether the question is public
            
        Returns:
            ProjectQuestion: The created question
        """
        project = ProjectService.get_project_by_id(project_id, user)
        
        # Check if project is not draft
        if project.is_draft:
            raise ValidationError("Vous ne pouvez pas poser de question sur un projet en brouillon.")
        
        question = ProjectQuestion.objects.create(
            user=user,
            project=project,
            question=question_text,
            is_public=is_public
        )
        
        return question
    
    @staticmethod
    def answer_project_question(user, question_id, answer_text):
        """
        Answer a project question.
        
        Args:
            user (User): Current user
            question_id (uuid): Question ID
            answer_text (str): Answer text
            
        Returns:
            ProjectQuestionAnswer: The created answer
            
        Raises:
            ResourceNotFoundError: If the question doesn't exist
            PermissionDeniedError: If the user is not the project creator
            ValidationError: If the question is already answered
        """
        try:
            question = ProjectQuestion.objects.get(id=question_id)
        except ProjectQuestion.DoesNotExist:
            raise ResourceNotFoundError("Question non trouvée.")
        
        # Check if user is the project creator
        if user != question.project.creator:
            raise PermissionDeniedError("Seul le créateur du projet peut répondre à cette question.")
        
        # Check if already answered
        if hasattr(question, 'answer'):
            raise ValidationError("Cette question a déjà été répondue.")
        
        answer = ProjectQuestionAnswer.objects.create(
            question=question,
            answered_by=user,
            answer=answer_text
        )
        
        return answer 