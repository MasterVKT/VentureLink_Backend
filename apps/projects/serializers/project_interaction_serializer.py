"""
Serializers for project interactions like interests, favorites, and Q&A.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.serializers import UserSerializer
from apps.projects.models.project_interaction import (
    ProjectInterest, ProjectFavorite, 
    ProjectQuestion, ProjectQuestionAnswer, ProjectReport
)


class ProjectInterestSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectInterest model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProjectInterest
        fields = [
            'id', 'user', 'project', 'message', 'status',
            'is_anonymous', 'investment_amount', 'investment_currency',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class ProjectInterestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project interest.
    """
    
    class Meta:
        model = ProjectInterest
        fields = [
            'project', 'message', 'is_anonymous',
            'investment_amount', 'investment_currency'
        ]
    
    def validate_project(self, value):
        """
        Validate that the project exists and is not a draft.
        """
        if value.is_draft:
            raise serializers.ValidationError(_('Vous ne pouvez pas exprimer d\'intérêt pour un projet en brouillon.'))
        
        user = self.context['request'].user
        if ProjectInterest.objects.filter(user=user, project=value).exists():
            raise serializers.ValidationError(_('Vous avez déjà exprimé un intérêt pour ce projet.'))
        
        return value
    
    def create(self, validated_data):
        """
        Create and return a new project interest instance.
        """
        return ProjectInterest.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class ProjectInterestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project interest (mainly for status updates).
    """
    
    class Meta:
        model = ProjectInterest
        fields = ['status']
        

class ProjectFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectFavorite model.
    """
    
    class Meta:
        model = ProjectFavorite
        fields = ['id', 'project', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_project(self, value):
        """
        Validate that the project exists.
        """
        user = self.context['request'].user
        if ProjectFavorite.objects.filter(user=user, project=value).exists():
            raise serializers.ValidationError(_('Ce projet est déjà dans vos favoris.'))
        
        return value
    
    def create(self, validated_data):
        """
        Create and return a new project favorite instance.
        """
        return ProjectFavorite.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class ProjectQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectQuestion model.
    """
    user = UserSerializer(read_only=True)
    has_answer = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectQuestion
        fields = ['id', 'user', 'project', 'question', 'is_public', 'is_answered', 'has_answer', 'created_at']
        read_only_fields = ['id', 'user', 'is_answered', 'created_at']
    
    def get_has_answer(self, obj):
        """Check if the question has an answer."""
        return hasattr(obj, 'answer')


class ProjectQuestionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project questions.
    """
    
    class Meta:
        model = ProjectQuestion
        fields = ['project', 'question', 'is_public']
    
    def create(self, validated_data):
        """
        Create and return a new project question instance.
        """
        return ProjectQuestion.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class ProjectQuestionAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectQuestionAnswer model.
    """
    answered_by = UserSerializer(read_only=True)
    question_text = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectQuestionAnswer
        fields = ['id', 'question', 'question_text', 'answered_by', 'answer', 'created_at']
        read_only_fields = ['id', 'answered_by', 'created_at']
    
    def get_question_text(self, obj):
        """Get the text of the question."""
        return obj.question.question


class ProjectQuestionAnswerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project question answers.
    """
    
    class Meta:
        model = ProjectQuestionAnswer
        fields = ['question', 'answer']
    
    def validate_question(self, value):
        """
        Validate that the question exists and is not already answered.
        """
        if value.is_answered:
            raise serializers.ValidationError(_('Cette question a déjà été répondue.'))
        
        # Vérifier que l'utilisateur est le créateur du projet
        user = self.context['request'].user
        if value.project.creator != user:
            raise serializers.ValidationError(_('Seul le créateur du projet peut répondre à cette question.'))
        
        return value
    
    def create(self, validated_data):
        """
        Create and return a new project question answer instance.
        """
        return ProjectQuestionAnswer.objects.create(
            answered_by=self.context['request'].user,
            **validated_data
        ) 


class ProjectReportSerializer(serializers.ModelSerializer):
    """Serializer for ProjectReport model (read/list)."""
    user = UserSerializer(read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = ProjectReport
        fields = [
            'id', 'user', 'project', 'project_title', 'reason', 'description', 'is_resolved', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_resolved', 'created_at']


class ProjectReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a project report."""

    class Meta:
        model = ProjectReport
        fields = ['project', 'reason', 'description']

    def validate_project(self, value):
        user = self.context['request'].user
        if value.creator == user:
            raise serializers.ValidationError(_('Vous ne pouvez pas signaler votre propre projet.'))
        if ProjectReport.objects.filter(user=user, project=value).exists():
            raise serializers.ValidationError(_('Vous avez déjà signalé ce projet.'))
        if value.is_draft:
            raise serializers.ValidationError(_('Vous ne pouvez pas signaler un projet en brouillon.'))
        return value

    def create(self, validated_data):
        return ProjectReport.objects.create(
            user=self.context['request'].user,
            **validated_data
        ) 