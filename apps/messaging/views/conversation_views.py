"""
ViewSets for conversation models.
"""
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

from apps.messaging.models import Conversation, ConversationParticipant
from apps.messaging.serializers import (
    ConversationSerializer, ConversationListSerializer, 
    ConversationCreateSerializer, ConversationParticipantSerializer,
    ConversationParticipantCreateSerializer
)
from apps.messaging.services import ConversationService


class ConversationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for conversations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return ConversationListSerializer
        elif self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def get_queryset(self):
        """
        Return conversations where the current user is a participant.
        """
        # Get filters from query params
        filters = {}
        
        status = self.request.query_params.get('status')
        if status:
            filters['status'] = status
            
        conversation_type = self.request.query_params.get('type')
        if conversation_type:
            filters['type'] = conversation_type
            
        search = self.request.query_params.get('search')
        if search:
            filters['search'] = search
            
        project_id = self.request.query_params.get('project_id')
        if project_id:
            filters['project_id'] = project_id
        
        # Get ordering from query params
        ordering = self.request.query_params.get('ordering')
        
        return ConversationService.get_conversations(
            user=self.request.user,
            filters=filters,
            ordering=ordering
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new conversation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            conversation = ConversationService.create_conversation(
                user=request.user,
                data=serializer.validated_data
            )
            
            # Return the created conversation with the full serializer
            return Response(
                ConversationSerializer(
                    conversation,
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
        Update a conversation.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            conversation = ConversationService.update_conversation(
                conversation_id=instance.id,
                user=request.user,
                data=serializer.validated_data
            )
            
            return Response(
                self.get_serializer(conversation).data
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """
        Add a participant to a conversation.
        """
        serializer = ConversationParticipantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            participant = ConversationService.add_participant(
                conversation_id=pk,
                user=request.user,
                participant_data=serializer.validated_data
            )
            
            return Response(
                ConversationParticipantSerializer(participant).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='remove-participant/(?P<participant_id>[^/.]+)')
    def remove_participant(self, request, pk=None, participant_id=None):
        """
        Remove a participant from a conversation.
        """
        try:
            success = ConversationService.remove_participant(
                conversation_id=pk,
                user=request.user,
                participant_id=participant_id
            )
            
            return Response(
                {'success': success},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """
        Mark all messages in a conversation as read.
        """
        try:
            count = ConversationService.mark_conversation_as_read(
                conversation_id=pk,
                user=request.user
            )
            
            return Response(
                {'count': count},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='participants')
    def participants(self, request, pk=None):
        """
        Get participants of a conversation.
        """
        try:
            conversation = self.get_object()
            participants = ConversationParticipant.objects.filter(
                conversation=conversation
            ).select_related('user')
            
            serializer = ConversationParticipantSerializer(
                participants,
                many=True,
                context={'request': request}
            )
            
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='direct')
    def direct_conversation(self, request):
        """
        Get or create a direct conversation with another user.
        """
        recipient_id = request.data.get('recipient_id')
        if not recipient_id:
            return Response(
                {'detail': 'L\'ID du destinataire est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation, created = ConversationService.get_or_create_direct_conversation(
                user=request.user,
                recipient_id=recipient_id
            )
            
            return Response(
                ConversationSerializer(
                    conversation,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )