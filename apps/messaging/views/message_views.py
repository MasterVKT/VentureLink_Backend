"""
ViewSets for message models.
"""
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

from apps.messaging.models import Message, MessageAttachment, MessageRead
from apps.messaging.serializers import (
    MessageSerializer, MessageListSerializer, MessageCreateSerializer,
    MessageAttachmentSerializer, MessageReadSerializer
)
from apps.messaging.services import MessageService, ConversationService


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for messages in a conversation.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return MessageListSerializer
        elif self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """
        Return messages for the specified conversation with filtering.
        """
        # Get conversation ID from URL
        conversation_id = self.kwargs.get('conversation_pk')
        
        # Get filters from query params
        filters = {}
        
        search = self.request.query_params.get('search')
        if search:
            filters['search'] = search
            
        message_type = self.request.query_params.get('type')
        if message_type:
            filters['type'] = message_type
            
        sender_id = self.request.query_params.get('sender_id')
        if sender_id:
            filters['sender_id'] = sender_id
            
        start_date = self.request.query_params.get('start_date')
        if start_date:
            filters['start_date'] = start_date
            
        end_date = self.request.query_params.get('end_date')
        if end_date:
            filters['end_date'] = end_date
        
        # Get pagination parameters
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = 50
        else:
            limit = 50
            
        offset = self.request.query_params.get('offset')
        if offset:
            try:
                offset = int(offset)
            except ValueError:
                offset = 0
        else:
            offset = 0
        
        return MessageService.get_messages(
            conversation_id=conversation_id,
            user=self.request.user,
            filters=filters,
            limit=limit,
            offset=offset
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new message in a conversation.
        """
        # Get conversation ID from URL
        conversation_id = self.kwargs.get('conversation_pk')
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Ensure conversation exists and user has access
            conversation = ConversationService.get_conversation_by_id(
                conversation_id=conversation_id,
                user=request.user
            )
            
            # Add conversation to serializer context
            serializer.context['conversation'] = conversation
            
            # Create message
            message = serializer.save()
            
            # Mark as read for the sender
            MessageService.mark_message_as_read(
                message_id=message.id,
                user=request.user
            )
            
            # Return created message
            return Response(
                MessageSerializer(
                    message,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Update a message (content only).
        """
        instance = self.get_object()
        
        try:
            # Validate that user is the sender
            if instance.sender != request.user:
                return Response(
                    {'detail': 'Vous ne pouvez modifier que vos propres messages.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update message
            message = MessageService.update_message(
                message_id=instance.id,
                user=request.user,
                data=request.data
            )
            
            return Response(
                self.get_serializer(message).data
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete (mark as deleted) a message.
        """
        instance = self.get_object()
        
        try:
            # Delete message
            success = MessageService.delete_message(
                message_id=instance.id,
                user=request.user
            )
            
            return Response(
                {'success': success},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, conversation_pk=None, pk=None):
        """
        Mark a message as read.
        """
        try:
            # Mark message as read
            read_receipt = MessageService.mark_message_as_read(
                message_id=pk,
                user=request.user
            )
            
            if read_receipt:
                return Response(
                    MessageReadSerializer(read_receipt).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'detail': 'Message déjà lu ou envoyé par vous-même.'},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='replies')
    def replies(self, request, conversation_pk=None, pk=None):
        """
        Get replies to a message.
        """
        try:
            # Get message
            message = MessageService.get_message_by_id(
                message_id=pk,
                user=request.user
            )
            
            # Get replies
            replies = message.replies.all().order_by('created_at')
            
            return Response(
                MessageListSerializer(
                    replies,
                    many=True,
                    context={'request': request}
                ).data
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MessageAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for message attachments.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageAttachmentSerializer
    
    def get_queryset(self):
        """
        Return attachments for the specified message.
        """
        # Get conversation and message IDs from URL
        conversation_id = self.kwargs.get('conversation_pk')
        message_id = self.kwargs.get('message_pk')
        
        # Ensure message exists and user has access
        try:
            message = MessageService.get_message_by_id(
                message_id=message_id,
                user=self.request.user
            )
            
            # Return attachments
            return message.attachments.all()
        except Exception:
            return MessageAttachment.objects.none() 