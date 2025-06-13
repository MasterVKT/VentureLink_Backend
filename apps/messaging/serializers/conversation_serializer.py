"""
Serializers for conversation models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.serializers import UserSerializer
from apps.projects.serializers import ProjectListSerializer
from apps.messaging.models import Conversation, ConversationParticipant


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for ConversationParticipant model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'conversation', 'user', 'is_admin', 'last_read_at',
            'nickname', 'status', 'muted_until', 'created_at'
        ]
        read_only_fields = ['id', 'conversation', 'created_at']


class ConversationParticipantCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a ConversationParticipant.
    """
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'user_id', 'is_admin', 'nickname'
        ]
    
    def create(self, validated_data):
        conversation = self.context.get('conversation')
        user_id = validated_data.pop('user_id')
        
        return ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=user_id,
            **validated_data
        )


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model with details.
    """
    participants = UserSerializer(many=True, read_only=True)
    project = ProjectListSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'conversation_type', 'status', 'participants',
            'project', 'last_message_at', 'unread_count', 'last_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message_at']
    
    def get_unread_count(self, obj):
        """
        Get the number of unread messages for the current user.
        """
        user = self.context.get('request').user
        try:
            participant = obj.conversation_participants.get(user=user)
            
            # If never read, count all messages
            if not participant.last_read_at:
                return obj.messages.count()
            
            # Otherwise, count messages after last read
            return obj.messages.filter(
                created_at__gt=participant.last_read_at
            ).count()
        except ConversationParticipant.DoesNotExist:
            return 0
    
    def get_last_message(self, obj):
        """
        Get the last message in the conversation.
        """
        try:
            message = obj.messages.order_by('-created_at').first()
            if message:
                return {
                    'id': message.id,
                    'content': message.content[:100] + ('...' if len(message.content) > 100 else ''),
                    'sender_name': message.sender.get_full_name() if message.sender else 'Système',
                    'created_at': message.created_at,
                    'message_type': message.message_type
                }
        except Exception:
            pass
        return None


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing conversations.
    """
    participant_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'conversation_type', 'status', 'participant_count',
            'project_title', 'last_message_at', 'unread_count', 'last_message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_message_at']
    
    def get_participant_count(self, obj):
        """
        Get the number of participants.
        """
        return obj.participants.count()
    
    def get_project_title(self, obj):
        """
        Get the title of the associated project, if any.
        """
        return obj.project.title if obj.project else None
    
    def get_unread_count(self, obj):
        """
        Get the number of unread messages for the current user.
        """
        user = self.context.get('request').user
        try:
            participant = obj.conversation_participants.get(user=user)
            
            # If never read, count all messages
            if not participant.last_read_at:
                return obj.messages.count()
            
            # Otherwise, count messages after last read
            return obj.messages.filter(
                created_at__gt=participant.last_read_at
            ).count()
        except ConversationParticipant.DoesNotExist:
            return 0
    
    def get_last_message(self, obj):
        """
        Get the last message in the conversation.
        """
        try:
            message = obj.messages.order_by('-created_at').first()
            if message:
                return {
                    'content': message.content[:50] + ('...' if len(message.content) > 50 else ''),
                    'sender_name': message.sender.get_full_name() if message.sender else 'Système',
                    'created_at': message.created_at
                }
        except Exception:
            pass
        return None


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new conversation.
    """
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True,
        min_length=1
    )
    project_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = Conversation
        fields = [
            'title', 'conversation_type', 'participant_ids', 'project_id'
        ]
    
    def validate(self, data):
        """
        Validate conversation creation data.
        """
        conversation_type = data.get('conversation_type')
        title = data.get('title')
        project_id = data.get('project_id')
        
        # Title is required for group conversations
        if conversation_type == Conversation.TYPE_GROUP and not title:
            raise serializers.ValidationError({
                'title': _('Le titre est obligatoire pour les conversations de groupe.')
            })
        
        # Project is required for project conversations
        if conversation_type == Conversation.TYPE_PROJECT and not project_id:
            raise serializers.ValidationError({
                'project_id': _('L\'ID du projet est obligatoire pour les conversations de projet.')
            })
        
        # For direct messages, only 1 other participant is allowed
        if conversation_type == Conversation.TYPE_DIRECT and len(data.get('participant_ids', [])) != 1:
            raise serializers.ValidationError({
                'participant_ids': _('Les messages directs ne peuvent avoir qu\'un seul destinataire.')
            })
            
        return data 