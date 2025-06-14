"""
Serializers for the Project models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.projects.models.project import Project, ProjectCategory, ProjectTag


class ProjectCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectCategory model.
    """
    
    class Meta:
        model = ProjectCategory
        fields = ['id', 'name_fr', 'name_en', 'icon', 'description_fr', 'description_en']


class ProjectTagSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectTag model.
    """
    
    class Meta:
        model = ProjectTag
        fields = ['id', 'name_fr', 'name_en']


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing projects with minimal information.
    """
    category = ProjectCategorySerializer(read_only=True)
    tags = ProjectTagSerializer(many=True, read_only=True)
    creator_name = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    media_urls = serializers.SerializerMethodField()  # 🔥 NOUVEAU : tous les médias
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'short_description', 'category', 'tags',
            'stage', 'funding_min', 'funding_max', 'funding_currency',
            'location_country', 'location_city', 'creator_name',
            'primary_image_url', 'media_urls', 'views_count', 'interests_count',
            'favorites_count', 'is_premium', 'is_featured', 'is_verified',
            'verified_at', 'verification_status_display', 'published_at'
        ]
    
    def get_creator_name(self, obj):
        """Return the creator's name."""
        return obj.creator.get_full_name()
    
    def get_primary_image_url(self, obj):
        """Return the URL of the primary image if it exists."""
        primary_image = obj.primary_image
        if primary_image and primary_image.file:
            return primary_image.file.url
        return None
    
    def get_media_urls(self, obj):
        """Retourne tous les médias du projet pour le frontend."""
        return [
            {
                'id': str(media.id),
                'url': media.file.url if media.file else None,
                'type': media.media_type,
                'title': media.title,
                'description': media.description,
                'is_primary': media.is_primary,
                'order': media.order
            }
            for media in obj.media.order_by('order', '-created_at')
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for a detailed view of a project.
    """
    category = ProjectCategorySerializer(read_only=True)
    tags = ProjectTagSerializer(many=True, read_only=True)
    creator_name = serializers.SerializerMethodField()
    creator_id = serializers.SerializerMethodField()
    creator_profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'short_description', 'full_description',
            'category', 'tags', 'stage', 'funding_min', 'funding_max',
            'funding_currency', 'location_country', 'location_city',
            'creator_id', 'creator_name', 'creator_profile_picture',
            'views_count', 'interests_count', 'favorites_count',
            'is_premium', 'is_featured', 'is_verified', 'verified_at',
            'verification_status_display', 'is_draft', 'status',
            'published_at', 'created_at', 'updated_at', 'video_url'
        ]
        read_only_fields = ['views_count', 'interests_count', 'favorites_count', 
                           'is_verified', 'verified_at', 'verification_status_display']
    
    def get_creator_name(self, obj):
        """Return the creator's name."""
        return obj.creator.get_full_name()
    
    def get_creator_id(self, obj):
        """Return the creator's ID."""
        return str(obj.creator.id)
    
    def get_creator_profile_picture(self, obj):
        """Return the creator's profile picture URL if it exists."""
        if hasattr(obj.creator, 'profile') and obj.creator.profile.profile_picture:
            return obj.creator.profile.profile_picture.url
        return None


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new project.
    """
    
    class Meta:
        model = Project
        fields = [
            'title', 'short_description', 'full_description',
            'category', 'stage', 'funding_min', 'funding_max',
            'funding_currency', 'location_country', 'location_city',
            'tags', 'is_draft', 'video_url'
        ]
    
    def validate(self, data):
        """
        Custom validation for creating a project.
        """
        # Validate funding values
        funding_min = data.get('funding_min')
        funding_max = data.get('funding_max')
        
        if funding_min and funding_max and funding_min > funding_max:
            raise serializers.ValidationError({
                'funding_min': _('Le financement minimum ne peut pas être supérieur au financement maximum.')
            })
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new project instance.
        """
        tags = validated_data.pop('tags', [])
        
        project = Project.objects.create(
            creator=self.context['request'].user,
            **validated_data
        )
        
        # Add tags
        if tags:
            project.tags.set(tags)
        
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing project.
    """
    
    class Meta:
        model = Project
        fields = [
            'title', 'short_description', 'full_description',
            'category', 'stage', 'funding_min', 'funding_max',
            'funding_currency', 'location_country', 'location_city',
            'tags', 'is_draft', 'video_url'
        ]
    
    def validate(self, data):
        """
        Custom validation for updating a project.
        """
        # Validate funding values
        funding_min = data.get('funding_min')
        funding_max = data.get('funding_max')
        
        if funding_min and funding_max and funding_min > funding_max:
            raise serializers.ValidationError({
                'funding_min': _('Le financement minimum ne peut pas être supérieur au financement maximum.')
            })
        
        return data
    
    def update(self, instance, validated_data):
        """
        Update and return an existing project instance.
        """
        tags = validated_data.pop('tags', None)
        
        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update tags if provided
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class ProjectVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for project verification by administrators.
    """
    verification_notes = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text=_('Notes optionnelles sur la vérification')
    )
    
    class Meta:
        model = Project
        fields = ['is_verified', 'verification_notes']
    
    def validate(self, data):
        """
        Validate that only staff users can perform verification actions.
        """
        request = self.context.get('request')
        if request and not request.user.is_staff:
            raise serializers.ValidationError(
                _('Seuls les administrateurs peuvent effectuer des actions de vérification.')
            )
        return data
    
    def update(self, instance, validated_data):
        """
        Update the project verification status.
        """
        verification_notes = validated_data.get('verification_notes', '')
        is_verified = validated_data.get('is_verified')
        request_user = self.context['request'].user
        
        if is_verified:
            instance.verify_project(request_user, verification_notes)
        else:
            instance.unverify_project(request_user, verification_notes)
        
        return instance


class ProjectPublishSerializer(serializers.ModelSerializer):
    """
    Serializer for publishing a project.
    """
    
    class Meta:
        model = Project
        fields = ['is_draft']
    
    def validate_is_draft(self, value):
        """
        Validate that is_draft is being set to False.
        """
        if value:
            raise serializers.ValidationError(_('Ce sérialiseur est réservé à la publication. is_draft doit être False.'))
        return value
    
    def update(self, instance, validated_data):
        """
        Update the is_draft field and set published_at date.
        """
        from django.utils import timezone
        
        instance.is_draft = False
        instance.published_at = timezone.now()
        instance.save()
        
        return instance 