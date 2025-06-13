"""
Serializers for project needs and skills.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.projects.models.project_needs import ProjectNeeds, ProjectSkillsNeeded


class ProjectNeedsSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectNeeds model.
    """
    
    class Meta:
        model = ProjectNeeds
        fields = [
            'id', 'resource_type', 'title', 'description', 
            'amount', 'is_critical', 'deadline', 
            'is_satisfied', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProjectNeedsCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project needs.
    """
    
    class Meta:
        model = ProjectNeeds
        fields = [
            'resource_type', 'title', 'description', 
            'amount', 'is_critical', 'deadline'
        ]
    
    def create(self, validated_data):
        """
        Create and return a new project need instance.
        """
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError(_('L\'ID du projet est requis.'))
        
        return ProjectNeeds.objects.create(
            project_id=project_id,
            **validated_data
        )


class ProjectNeedsUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project needs.
    """
    
    class Meta:
        model = ProjectNeeds
        fields = [
            'resource_type', 'title', 'description', 
            'amount', 'is_critical', 'deadline', 'is_satisfied'
        ]


class ProjectSkillsNeededSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectSkillsNeeded model.
    """
    
    class Meta:
        model = ProjectSkillsNeeded
        fields = [
            'id', 'name', 'description', 'priority', 
            'required_level', 'is_satisfied', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProjectSkillsNeededCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project skills needed.
    """
    
    class Meta:
        model = ProjectSkillsNeeded
        fields = [
            'name', 'description', 'priority', 'required_level'
        ]
    
    def create(self, validated_data):
        """
        Create and return a new project skill needed instance.
        """
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError(_('L\'ID du projet est requis.'))
        
        return ProjectSkillsNeeded.objects.create(
            project_id=project_id,
            **validated_data
        )


class ProjectSkillsNeededUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project skills needed.
    """
    
    class Meta:
        model = ProjectSkillsNeeded
        fields = [
            'name', 'description', 'priority', 
            'required_level', 'is_satisfied'
        ] 