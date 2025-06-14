"""
Sérialiseurs pour les commentaires et likes de commentaires.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from apps.content.models import Comment, CommentLike
from apps.users.serializers.user_serializer import UserSimpleSerializer


class CommentLikeSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les likes de commentaires.
    """
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la lecture des commentaires.
    """
    author = UserSimpleSerializer(read_only=True)
    likes = CommentLikeSerializer(many=True, read_only=True)
    user_has_liked = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()
    parent_id = serializers.UUIDField(source='parent.id', read_only=True)
    depth = serializers.ReadOnlyField()
    can_have_replies = serializers.ReadOnlyField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'parent_id', 'depth',
            'likes_count', 'replies_count', 'likes', 'user_has_liked',
            'is_active', 'is_edited', 'edited_at', 'can_have_replies',
            'content_type_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'parent_id', 'depth', 'likes_count', 
            'replies_count', 'likes', 'user_has_liked', 'is_edited', 
            'edited_at', 'can_have_replies', 'content_type_name',
            'created_at', 'updated_at'
        ]
    
    def get_user_has_liked(self, obj):
        """Vérifie si l'utilisateur connecté a liké ce commentaire."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_content_type_name(self, obj):
        """Retourne le nom du type de contenu commenté."""
        if obj.content_type:
            return obj.content_type.name
        return None


class CommentTreeSerializer(CommentSerializer):
    """
    Sérialiseur pour les commentaires avec leurs réponses (structure arborescente).
    """
    replies = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']
    
    def get_replies(self, obj):
        """Récupère les réponses à ce commentaire."""
        if obj.replies_count > 0:
            replies = obj.replies.filter(is_active=True).order_by('created_at')
            return CommentTreeSerializer(
                replies, 
                many=True, 
                context=self.context
            ).data
        return []


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de commentaires.
    """
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.CharField(write_only=True)
    parent_id = serializers.UUIDField(required=False, write_only=True)
    
    class Meta:
        model = Comment
        fields = ['content', 'content_type', 'object_id', 'parent_id']
    
    def validate_content_type(self, value):
        """Validation du type de contenu."""
        try:
            app_label, model_name = value.split('.')
            content_type = ContentType.objects.get_by_natural_key(app_label, model_name)
            return content_type
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                _("Type de contenu invalide. Format attendu : 'app.model'")
            )
    
    def validate_parent_id(self, value):
        """Validation du commentaire parent."""
        if value:
            try:
                parent = Comment.objects.get(id=value, is_active=True)
                # Vérifier la profondeur maximale
                if not parent.can_have_replies:
                    raise serializers.ValidationError(
                        _("Ce commentaire ne peut plus recevoir de réponses.")
                    )
                return parent
            except Comment.DoesNotExist:
                raise serializers.ValidationError(
                    _("Commentaire parent inexistant.")
                )
        return None
    
    def validate(self, attrs):
        """Validations générales."""
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')
        parent = attrs.get('parent_id')
        
        # Vérifier que l'objet existe
        try:
            model_class = content_type.model_class()
            target_object = model_class.objects.get(id=object_id)
            
            # Vérifier que l'objet peut être commenté (pour les projets et publications)
            if hasattr(target_object, 'can_be_commented'):
                if not target_object.can_be_commented:
                    raise serializers.ValidationError(
                        _("Cet objet ne peut pas être commenté.")
                    )
            
        except model_class.DoesNotExist:
            raise serializers.ValidationError(
                _("L'objet à commenter n'existe pas.")
            )
        
        # Si c'est une réponse, vérifier que le parent concerne le même objet
        if parent:
            if (parent.content_type != content_type or 
                str(parent.object_id) != str(object_id)):
                raise serializers.ValidationError(
                    _("Le commentaire parent doit concerner le même objet.")
                )
        
        return attrs
    
    def create(self, validated_data):
        """Création du commentaire."""
        # Extraire les données spéciales
        content_type = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')
        parent = validated_data.pop('parent_id', None)
        
        # Créer le commentaire
        comment = Comment.objects.create(
            author=self.context['request'].user,
            content_type=content_type,
            object_id=str(object_id),
            parent=parent,
            **validated_data
        )
        
        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour des commentaires.
    """
    class Meta:
        model = Comment
        fields = ['content']
    
    def update(self, instance, validated_data):
        """Mise à jour du commentaire avec marquage d'édition."""
        instance.content = validated_data.get('content', instance.content)
        instance.is_edited = True
        from django.utils import timezone
        instance.edited_at = timezone.now()
        instance.save()
        return instance
    
    def validate(self, attrs):
        """Vérifier que l'utilisateur peut modifier ce commentaire."""
        request = self.context.get('request')
        if request and request.user != self.instance.author:
            if not request.user.is_staff:
                raise serializers.ValidationError(
                    _("Vous ne pouvez modifier que vos propres commentaires.")
                )
        return attrs 