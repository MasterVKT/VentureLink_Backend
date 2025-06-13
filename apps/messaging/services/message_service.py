"""
Service layer for message operations.
"""
from django.db.models import Q
from django.utils import timezone

from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.messaging.models import Message, MessageAttachment, MessageRead
from apps.messaging.services.conversation_service import ConversationService


class MessageService:
    """
    Service for message operations.
    """
    
    @staticmethod
    def get_messages(conversation_id, user, filters=None, limit=50, offset=0):
        """
        Get messages for a conversation with pagination.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            filters (dict, optional): Filters to apply
            limit (int): Maximum number of messages to return
            offset (int): Offset for pagination
            
        Returns:
            QuerySet: Filtered messages
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist
        """
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Start with conversation messages
        queryset = Message.objects.filter(
            conversation=conversation
        ).exclude(
            status=Message.STATUS_DELETED
        )
        
        # Apply search filter
        filters = filters or {}
        search = filters.get('search')
        if search:
            queryset = queryset.filter(content__icontains=search)
        
        # Apply type filter
        message_type = filters.get('type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)
        
        # Apply sender filter
        sender_id = filters.get('sender_id')
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
        
        # Apply date range filter
        start_date = filters.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
            
        end_date = filters.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Order by creation date (oldest first)
        queryset = queryset.order_by('-created_at')
        
        # Apply pagination
        if offset is not None and limit is not None:
            queryset = queryset[offset:offset + limit]
        
        return queryset
    
    @staticmethod
    def get_message_by_id(message_id, user):
        """
        Get a message by its ID if the user has access to the conversation.
        
        Args:
            message_id (uuid): Message ID
            user (User): Current user
            
        Returns:
            Message: The message
            
        Raises:
            ResourceNotFoundError: If the message doesn't exist or user can't access it
        """
        try:
            message = Message.objects.get(id=message_id)
            
            # Check if user has access to the conversation
            ConversationService.get_conversation_by_id(message.conversation_id, user)
            
            return message
        except Message.DoesNotExist:
            raise ResourceNotFoundError("Message non trouvé.")
    
    @staticmethod
    def create_message(conversation_id, user, data):
        """
        Create a new message in a conversation.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user (sender)
            data (dict): Message data
            
        Returns:
            Message: The created message
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist
            ValidationError: If the message data is invalid
        """
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Check if message is empty
        content = data.get('content', '').strip()
        if not content and not data.get('attachments'):
            raise ValidationError("Le message ne peut pas être vide.")
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            message_type=data.get('message_type', Message.TYPE_TEXT),
            content=content,
            parent_id=data.get('parent_id'),
            is_system_message=data.get('is_system_message', False),
            status=Message.STATUS_SENT
        )
        
        # Create attachments if provided
        attachments_data = data.get('attachments', [])
        for attachment_data in attachments_data:
            MessageAttachment.objects.create(
                message=message,
                **attachment_data
            )
        
        # Update conversation's last_message_at
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])
        
        return message
    
    @staticmethod
    def update_message(message_id, user, data):
        """
        Update a message.
        
        Args:
            message_id (uuid): Message ID
            user (User): Current user
            data (dict): Updated data
            
        Returns:
            Message: The updated message
            
        Raises:
            ResourceNotFoundError: If the message doesn't exist
            PermissionDeniedError: If the user is not the sender
            ValidationError: If the update is invalid
        """
        # Get message
        message = MessageService.get_message_by_id(message_id, user)
        
        # Check if user is the sender
        if message.sender_id != user.id:
            raise PermissionDeniedError("Vous ne pouvez modifier que vos propres messages.")
        
        # Check if message is too old to edit (15 minutes)
        if (timezone.now() - message.created_at).total_seconds() > 15 * 60:
            raise ValidationError("Ce message ne peut plus être modifié (plus de 15 minutes).")
        
        # Update content if provided
        if 'content' in data:
            content = data['content'].strip()
            if not content:
                raise ValidationError("Le contenu du message ne peut pas être vide.")
            message.content = content
        
        message.save()
        return message
    
    @staticmethod
    def delete_message(message_id, user):
        """
        Delete (mark as deleted) a message.
        
        Args:
            message_id (uuid): Message ID
            user (User): Current user
            
        Returns:
            bool: Success flag
            
        Raises:
            ResourceNotFoundError: If the message doesn't exist
            PermissionDeniedError: If the user can't delete the message
        """
        # Get message
        message = MessageService.get_message_by_id(message_id, user)
        
        # Check if user is the sender or an admin
        is_sender = message.sender_id == user.id
        
        # Check if user is an admin of the conversation
        is_admin = False
        try:
            participant = message.conversation.conversation_participants.get(user=user)
            is_admin = participant.is_admin
        except:
            pass
        
        if not (is_sender or is_admin):
            raise PermissionDeniedError("Vous ne pouvez supprimer que vos propres messages ou les messages des conversations que vous administrez.")
        
        # Mark as deleted
        message.status = Message.STATUS_DELETED
        message.save(update_fields=['status'])
        
        return True
    
    @staticmethod
    def mark_message_as_read(message_id, user):
        """
        Mark a message as read by a user.
        
        Args:
            message_id (uuid): Message ID
            user (User): Current user
            
        Returns:
            MessageRead: The read receipt
            
        Raises:
            ResourceNotFoundError: If the message doesn't exist
        """
        # Get message
        message = MessageService.get_message_by_id(message_id, user)
        
        # Skip if user is the sender
        if message.sender_id == user.id:
            return None
        
        # Create read receipt
        read_receipt, created = MessageRead.objects.get_or_create(
            message=message,
            user=user,
            defaults={'read_at': timezone.now()}
        )
        
        # Update participant's last_read_at if this is the newest message they've read
        try:
            participant = message.conversation.conversation_participants.get(user=user)
            
            if not participant.last_read_at or message.created_at > participant.last_read_at:
                participant.last_read_at = timezone.now()
                participant.save(update_fields=['last_read_at'])
        except:
            pass
        
        return read_receipt 