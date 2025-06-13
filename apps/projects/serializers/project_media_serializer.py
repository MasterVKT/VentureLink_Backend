"""
Serializers for project media models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.projects.models.project_media import ProjectMedia


class ProjectMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectMedia model.
    """
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectMedia
        fields = [
            'id', 'file', 'file_url', 'media_type', 'title', 
            'description', 'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file_url(self, obj):
        """Return the URL of the file."""
        if obj.file:
            return obj.file.url
        return None


class ProjectMediaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project media.
    """
    
    class Meta:
        model = ProjectMedia
        fields = [
            'file', 'media_type', 'title', 
            'description', 'is_primary', 'order'
        ]
    
    def create(self, validated_data):
        """
        Create and return a new project media instance.
        """
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError(_('L\'ID du projet est requis.'))
        
        return ProjectMedia.objects.create(
            project_id=project_id,
            **validated_data
        )


class ProjectMediaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project media.
    """
    
    class Meta:
        model = ProjectMedia
        fields = [
            'title', 'description', 
            'is_primary', 'order'
        ] 