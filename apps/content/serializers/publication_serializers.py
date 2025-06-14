"""
Sérialiseurs pour les publications et leurs médias.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.content.models import Publication, PublicationMedia, PublicationLike
from apps.users.serializers.user_serializer import UserSimpleSerializer


class PublicationMediaSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les médias de publication.
    """
    class Meta:
        model = PublicationMedia
        fields = [
            'id', 'file', 'media_type', 'title', 'description', 
            'alt_text', 'order', 'is_featured', 'file_size', 'created_at'
        ]
        read_only_fields = ['id', 'file_size', 'created_at']
    
    def validate_order(self, value):
        """Valider l'ordre (max 3 médias)."""
        if value > 2:
            raise serializers.ValidationError(
                _("L'ordre ne peut pas dépasser 2 (maximum 3 médias).")
            )
        return value


class PublicationLikeSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les likes de publication.
    """
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = PublicationLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PublicationListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des publications.
    """
    author = UserSimpleSerializer(read_only=True)
    featured_media = serializers.SerializerMethodField()
    tags_list = serializers.ReadOnlyField(source='get_tags_list')
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'summary', 'publication_type', 'domain',
            'author', 'status', 'published_at', 'views_count', 
            'likes_count', 'comments_count', 'is_featured', 
            'is_pinned', 'is_sponsored', 'sponsor_name',
            'featured_media', 'tags_list', 'user_has_liked', 'slug'
        ]
        read_only_fields = [
            'id', 'author', 'views_count', 'likes_count', 
            'comments_count', 'featured_media', 'tags_list', 
            'user_has_liked', 'slug'
        ]
    
    def get_featured_media(self, obj):
        """Récupère le média de couverture."""
        featured = obj.media.filter(is_featured=True).first()
        if featured:
            return PublicationMediaSerializer(featured).data
        return None
    
    def get_user_has_liked(self, obj):
        """Vérifie si l'utilisateur connecté a liké cette publication."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PublicationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur complet pour les publications.
    """
    author = UserSimpleSerializer(read_only=True)
    media = PublicationMediaSerializer(many=True, read_only=True)
    likes = PublicationLikeSerializer(many=True, read_only=True)
    tags_list = serializers.ReadOnlyField(source='get_tags_list')
    user_has_liked = serializers.SerializerMethodField()
    can_be_commented = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'content', 'summary', 'publication_type', 
            'domain', 'tags', 'tags_list', 'author', 'status', 
            'published_at', 'scheduled_for', 'views_count', 'likes_count', 
            'comments_count', 'shares_count', 'is_featured', 'is_pinned', 
            'allow_comments', 'is_sponsored', 'sponsor_name', 'sponsor_url',
            'meta_description', 'slug', 'media', 'likes', 'user_has_liked',
            'can_be_commented', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'published_at', 'views_count', 'likes_count', 
            'comments_count', 'shares_count', 'media', 'likes', 'tags_list',
            'user_has_liked', 'can_be_commented', 'is_published', 'slug',
            'created_at', 'updated_at'
        ]
    
    def get_user_has_liked(self, obj):
        """Vérifie si l'utilisateur connecté a liké cette publication."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PublicationCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de publications.
    """
    media_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True,
        max_length=3,
        help_text=_("Maximum 3 fichiers médias")
    )
    media_types = serializers.ListField(
        child=serializers.ChoiceField(choices=PublicationMedia.MEDIA_TYPE_CHOICES),
        required=False,
        write_only=True,
        max_length=3,
        help_text=_("Types des médias correspondants")
    )
    media_titles = serializers.ListField(
        child=serializers.CharField(max_length=100, required=False),
        required=False,
        write_only=True,
        max_length=3,
        help_text=_("Titres des médias correspondants")
    )
    
    class Meta:
        model = Publication
        fields = [
            'title', 'content', 'summary', 'publication_type', 'domain',
            'tags', 'status', 'scheduled_for', 'is_featured', 'is_pinned',
            'allow_comments', 'is_sponsored', 'sponsor_name', 'sponsor_url',
            'meta_description', 'media_files', 'media_types', 'media_titles'
        ]
    
    def validate(self, attrs):
        """Validations générales."""
        # Vérifier que l'utilisateur est admin
        request = self.context.get('request')
        if request and not request.user.is_staff:
            raise serializers.ValidationError(
                _("Seuls les administrateurs peuvent créer des publications.")
            )
        
        # Validation des médias
        media_files = attrs.get('media_files', [])
        media_types = attrs.get('media_types', [])
        media_titles = attrs.get('media_titles', [])
        
        if media_files:
            if len(media_files) != len(media_types):
                raise serializers.ValidationError(
                    _("Le nombre de fichiers doit correspondre au nombre de types.")
                )
            
            if media_titles and len(media_titles) != len(media_files):
                raise serializers.ValidationError(
                    _("Le nombre de titres doit correspondre au nombre de fichiers.")
                )
        
        # Validation du sponsoring
        if attrs.get('is_sponsored') and not attrs.get('sponsor_name'):
            raise serializers.ValidationError(
                _("Le nom du sponsor est requis pour un contenu sponsorisé.")
            )
        
        return attrs
    
    def create(self, validated_data):
        """Création de la publication avec ses médias."""
        # Extraire les données des médias
        media_files = validated_data.pop('media_files', [])
        media_types = validated_data.pop('media_types', [])
        media_titles = validated_data.pop('media_titles', [])
        
        # Créer la publication
        publication = Publication.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        
        # Créer les médias
        for i, media_file in enumerate(media_files):
            media_type = media_types[i] if i < len(media_types) else PublicationMedia.MEDIA_TYPE_IMAGE
            media_title = media_titles[i] if i < len(media_titles) else ''
            
            PublicationMedia.objects.create(
                publication=publication,
                file=media_file,
                media_type=media_type,
                title=media_title,
                order=i,
                is_featured=(i == 0)  # Le premier média est défini comme featured
            )
        
        return publication


class PublicationUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour des publications.
    """
    class Meta:
        model = Publication
        fields = [
            'title', 'content', 'summary', 'publication_type', 'domain',
            'tags', 'status', 'scheduled_for', 'is_featured', 'is_pinned',
            'allow_comments', 'is_sponsored', 'sponsor_name', 'sponsor_url',
            'meta_description'
        ]
    
    def validate(self, attrs):
        """Validations pour la mise à jour."""
        # Vérifier que l'utilisateur peut modifier (auteur ou admin)
        request = self.context.get('request')
        if request:
            if not (request.user == self.instance.author or request.user.is_staff):
                raise serializers.ValidationError(
                    _("Vous ne pouvez modifier que vos propres publications.")
                )
        
        # Validation du sponsoring
        is_sponsored = attrs.get('is_sponsored', self.instance.is_sponsored)
        sponsor_name = attrs.get('sponsor_name', self.instance.sponsor_name)
        
        if is_sponsored and not sponsor_name:
            raise serializers.ValidationError(
                _("Le nom du sponsor est requis pour un contenu sponsorisé.")
            )
        
        return attrs
    
    def update(self, instance, validated_data):
        """Mise à jour de la publication."""
        # Si le statut change vers PUBLISHED, mettre à jour published_at
        if (validated_data.get('status') == Publication.STATUS_PUBLISHED and 
            instance.status != Publication.STATUS_PUBLISHED):
            instance.published_at = timezone.now()
        
        return super().update(instance, validated_data) 