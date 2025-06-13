"""
Service layer for conversation operations.
"""
from django.db.models import Q, Count, Max, F, ExpressionWrapper, BooleanField
from django.utils import timezone

from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError
from apps.messaging.models import Conversation, ConversationParticipant
from apps.projects.models import Project


class ConversationService:
    """
    Service for conversation operations.
    """
    
    @staticmethod
    def get_conversations(user, filters=None, ordering=None):
        """
        Get conversations for a user with filtering and ordering.
        
        Args:
            user (User): Current user
            filters (dict, optional): Filters to apply
            ordering (str, optional): Field to order by
            
        Returns:
            QuerySet: Filtered conversations
        """
        filters = filters or {}
        
        # Start with conversations where user is a participant
        queryset = Conversation.objects.filter(
            participants=user,
            conversation_participants__status=Conversation.STATUS_ACTIVE
        )
        
        # Apply status filter
        status = filters.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply type filter
        conversation_type = filters.get('type')
        if conversation_type:
            queryset = queryset.filter(conversation_type=conversation_type)
        
        # Apply search filter
        search = filters.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(participants__first_name__icontains=search) |
                Q(participants__last_name__icontains=search) |
                Q(participants__email__icontains=search) |
                Q(project__title__icontains=search) |
                Q(messages__content__icontains=search)
            ).distinct()
        
        # Apply project filter
        project_id = filters.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Apply ordering
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            # Default ordering by last message
            queryset = queryset.order_by('-last_message_at', '-created_at')
        
        return queryset
    
    @staticmethod
    def get_conversation_by_id(conversation_id, user):
        """
        Get a conversation by its ID if the user is a participant.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            
        Returns:
            Conversation: The conversation
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist or user can't access it
        """
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=user
            )
            return conversation
        except Conversation.DoesNotExist:
            raise ResourceNotFoundError("Conversation non trouvée ou accès non autorisé.")
    
    @staticmethod
    def get_or_create_direct_conversation(user, recipient_id):
        """
        Get an existing direct conversation between two users or create a new one.
        
        Args:
            user (User): Current user
            recipient_id (uuid): The other participant's ID
            
        Returns:
            Conversation: The direct conversation
            bool: Whether the conversation was created
            
        Raises:
            ValidationError: If recipient doesn't exist
        """
        from apps.users.models import User
        
        # Check if recipient exists
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise ValidationError("Le destinataire spécifié n'existe pas.")
        
        # Check for existing direct conversation
        user_conversations = Conversation.objects.filter(
            conversation_type=Conversation.TYPE_DIRECT,
            participants=user
        )
        
        # Find conversations where the recipient is also a participant
        # and there are exactly 2 participants
        direct_conversation = user_conversations.filter(
            participants=recipient
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()
        
        # If found, return it
        if direct_conversation:
            return direct_conversation, False
        
        # Create new direct conversation
        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            status=Conversation.STATUS_ACTIVE
        )
        
        # Add participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user,
            is_admin=True
        )
        
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=recipient
        )
        
        return conversation, True
    
    @staticmethod
    def create_conversation(user, data):
        """
        Create a new conversation.
        
        Args:
            user (User): Current user (creator)
            data (dict): Conversation data including participant_ids
            
        Returns:
            Conversation: The created conversation
            
        Raises:
            ValidationError: If the data is invalid
        """
        from apps.users.models import User
        
        conversation_type = data.get('conversation_type')
        title = data.get('title')
        participant_ids = data.get('participant_ids', [])
        project_id = data.get('project_id')
        
        # Create conversation
        conversation = Conversation.objects.create(
            conversation_type=conversation_type,
            title=title,
            project_id=project_id,
            status=Conversation.STATUS_ACTIVE
        )
        
        # Add creator as admin participant
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user,
            is_admin=True
        )
        
        # Add other participants
        for participant_id in participant_ids:
            try:
                participant = User.objects.get(id=participant_id)
                
                # Skip if it's the creator (already added)
                if participant.id == user.id:
                    continue
                    
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=participant
                )
            except User.DoesNotExist:
                # Skip invalid users
                pass
        
        return conversation
    
    @staticmethod
    def update_conversation(conversation_id, user, data):
        """
        Update a conversation.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            data (dict): Updated data
            
        Returns:
            Conversation: The updated conversation
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist
            PermissionDeniedError: If the user can't update the conversation
        """
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Check if user is admin
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=user
            )
            
            if not participant.is_admin:
                raise PermissionDeniedError("Seuls les administrateurs peuvent modifier cette conversation.")
        except ConversationParticipant.DoesNotExist:
            raise PermissionDeniedError("Vous n'êtes pas membre de cette conversation.")
        
        # Update fields
        if 'title' in data:
            conversation.title = data['title']
            
        if 'status' in data:
            conversation.status = data['status']
        
        conversation.save()
        return conversation
    
    @staticmethod
    def add_participant(conversation_id, user, participant_data):
        """
        Add a participant to a conversation.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            participant_data (dict): Participant data including user_id
            
        Returns:
            ConversationParticipant: The created participant
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist
            PermissionDeniedError: If the user can't add participants
            ValidationError: If the user is already a participant
        """
        from apps.users.models import User
        
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Check if user is admin
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=user
            )
            
            if not participant.is_admin:
                raise PermissionDeniedError("Seuls les administrateurs peuvent ajouter des membres.")
        except ConversationParticipant.DoesNotExist:
            raise PermissionDeniedError("Vous n'êtes pas membre de cette conversation.")
        
        # Get new participant
        user_id = participant_data.get('user_id')
        
        try:
            new_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError("L'utilisateur spécifié n'existe pas.")
        
        # Check if already a participant
        if conversation.participants.filter(id=new_user.id).exists():
            raise ValidationError("Cet utilisateur est déjà membre de la conversation.")
        
        # Check direct message constraint
        if conversation.conversation_type == Conversation.TYPE_DIRECT:
            if conversation.participants.count() >= 2:
                raise ValidationError("Impossible d'ajouter plus de 2 participants à une conversation directe.")
        
        # Create participant
        is_admin = participant_data.get('is_admin', False)
        nickname = participant_data.get('nickname')
        
        return ConversationParticipant.objects.create(
            conversation=conversation,
            user=new_user,
            is_admin=is_admin,
            nickname=nickname
        )
    
    @staticmethod
    def remove_participant(conversation_id, user, participant_id):
        """
        Remove a participant from a conversation.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            participant_id (uuid): The participant to remove
            
        Returns:
            bool: Success flag
            
        Raises:
            ResourceNotFoundError: If the conversation or participant doesn't exist
            PermissionDeniedError: If the user can't remove participants
        """
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Check if user is admin or removing themselves
        try:
            user_participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=user
            )
        except ConversationParticipant.DoesNotExist:
            raise PermissionDeniedError("Vous n'êtes pas membre de cette conversation.")
        
        # Get participant to remove
        try:
            to_remove = ConversationParticipant.objects.get(
                conversation=conversation,
                user_id=participant_id
            )
        except ConversationParticipant.DoesNotExist:
            raise ResourceNotFoundError("Participant non trouvé dans cette conversation.")
        
        # Self-removal is always allowed
        is_self_removal = str(to_remove.user_id) == str(user.id)
        
        # Admin removal requires admin privileges
        if not is_self_removal and not user_participant.is_admin:
            raise PermissionDeniedError("Seuls les administrateurs peuvent retirer des membres.")
        
        # Check direct message constraint
        if conversation.conversation_type == Conversation.TYPE_DIRECT:
            # For direct messages, we archive the participant instead of removing
            to_remove.status = ConversationParticipant.STATUS_ARCHIVED
            to_remove.save()
        else:
            # For other conversations, we can remove the participant
            to_remove.delete()
        
        return True
    
    @staticmethod
    def mark_conversation_as_read(conversation_id, user):
        """
        Mark all messages in a conversation as read for a user.
        
        Args:
            conversation_id (uuid): Conversation ID
            user (User): Current user
            
        Returns:
            int: Number of messages marked as read
            
        Raises:
            ResourceNotFoundError: If the conversation doesn't exist
        """
        from apps.messaging.models import Message, MessageRead
        
        # Get conversation
        conversation = ConversationService.get_conversation_by_id(conversation_id, user)
        
        # Update last_read_at for the participant
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=user
            )
            
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        except ConversationParticipant.DoesNotExist:
            # This shouldn't happen since we verified user is a participant
            pass
        
        # Get unread messages
        unread_messages = Message.objects.filter(
            conversation=conversation
        ).exclude(
            read_receipts__user=user
        ).exclude(
            sender=user  # Don't mark user's own messages
        )
        
        # Create read receipts
        now = timezone.now()
        read_receipts = []
        
        for message in unread_messages:
            read_receipts.append(
                MessageRead(
                    message=message,
                    user=user,
                    read_at=now
                )
            )
        
        # Bulk create read receipts
        if read_receipts:
            MessageRead.objects.bulk_create(
                read_receipts,
                ignore_conflicts=True  # Ignore duplicates
            )
        
        return len(read_receipts) 