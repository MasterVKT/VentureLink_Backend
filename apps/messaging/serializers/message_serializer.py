"""
Serializers for message models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.serializers import UserSerializer
from apps.messaging.models import Message, MessageAttachment, MessageRead


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageAttachment model.
    """
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'message', 'file', 'file_name', 'file_size', 
            'file_type', 'thumbnail', 'created_at'
        ]
        read_only_fields = ['id', 'message', 'created_at']


class MessageAttachmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a message attachment.
    """
    
    class Meta:
        model = MessageAttachment
        fields = [
            'file', 'file_name', 'file_size', 'file_type', 'thumbnail'
        ]


class MessageReadSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageRead model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = [
            'id', 'message', 'user', 'read_at'
        ]
        read_only_fields = ['id', 'message', 'read_at']


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model with details.
    """
    sender = UserSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    read_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'message_type', 'content',
            'status', 'parent', 'is_system_message', 'attachments',
            'read_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']
    
    def get_read_by(self, obj):
        """
        Get a list of users who have read the message.
        """
        reads = obj.read_receipts.all()
        return [
            {
                'user_id': read.user_id,
                'user_name': read.user.get_full_name() if read.user else None,
                'read_at': read.read_at
            }
            for read in reads
        ]


class MessageListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing messages.
    """
    sender_name = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender_name', 'message_type', 'content',
            'status', 'is_system_message', 'attachment_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_sender_name(self, obj):
        """
        Get the name of the sender.
        """
        if obj.is_system_message:
            return "Système"
        return obj.sender.get_full_name() if obj.sender else "Inconnu"
    
    def get_attachment_count(self, obj):
        """
        Get the number of attachments.
        """
        return obj.attachments.count()


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new message.
    """
    attachments = MessageAttachmentCreateSerializer(many=True, required=False)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = Message
        fields = [
            'message_type', 'content', 'parent_id', 'is_system_message', 'attachments'
        ]
    
    def create(self, validated_data):
        """
        Create a message with attachments if provided.
        """
        attachments_data = validated_data.pop('attachments', None)
        parent_id = validated_data.pop('parent_id', None)
        
        # Get conversation from context
        conversation = self.context.get('conversation')
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=self.context.get('request').user,
            parent_id=parent_id,
            **validated_data
        )
        
        # Create attachments if provided
        if attachments_data:
            for attachment_data in attachments_data:
                MessageAttachment.objects.create(
                    message=message,
                    **attachment_data
                )
        
        # Update conversation's last_message_at
        from django.utils import timezone
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        return message 