"""
Signal handlers for the messaging application.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.messaging.models import Message, MessageRead, Conversation, ConversationParticipant


@receiver(post_save, sender=Message)
def update_conversation_last_message(sender, instance, created, **kwargs):
    """
    Update the conversation's last_message_at timestamp when a new message is created.
    """
    if created and instance.status != Message.STATUS_DELETED:
        conversation = instance.conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])


@receiver(post_save, sender=Message)
def create_read_receipt_for_sender(sender, instance, created, **kwargs):
    """
    Create a read receipt for the sender when a new message is created.
    """
    if created and instance.sender and not instance.is_system_message:
        MessageRead.objects.create(
            message=instance,
            user=instance.sender,
            read_at=timezone.now()
        )


@receiver(post_save, sender=MessageRead)
def update_participant_last_read(sender, instance, created, **kwargs):
    """
    Update the participant's last_read_at timestamp when a message is marked as read.
    """
    if created:
        try:
            participant = ConversationParticipant.objects.get(
                conversation=instance.message.conversation,
                user=instance.user
            )
            
            # Only update if this message is newer than the last read time
            if not participant.last_read_at or instance.message.created_at > participant.last_read_at:
                participant.last_read_at = timezone.now()
                participant.save(update_fields=['last_read_at'])
        except ConversationParticipant.DoesNotExist:
            pass


@receiver(post_save, sender=Conversation)
def mark_conversation_creator_as_admin(sender, instance, created, **kwargs):
    """
    Make the first participant in a new conversation an admin.
    """
    if created:
        # For system-created conversations, we might need to add this logic
        pass  # This will be handled explicitly in the service


@receiver(pre_save, sender=Message)
def handle_message_status_change(sender, instance, **kwargs):
    """
    Handle changes to message status.
    """
    if instance.pk:  # Only for existing messages
        try:
            old_instance = Message.objects.get(pk=instance.pk)
            
            # If message was deleted, update conversation last_message_at
            if old_instance.status != Message.STATUS_DELETED and instance.status == Message.STATUS_DELETED:
                # Get the last non-deleted message
                last_message = Message.objects.filter(
                    conversation=instance.conversation
                ).exclude(
                    status=Message.STATUS_DELETED
                ).exclude(
                    pk=instance.pk
                ).order_by('-created_at').first()
                
                if last_message:
                    instance.conversation.last_message_at = last_message.created_at
                else:
                    instance.conversation.last_message_at = None
                    
                instance.conversation.save(update_fields=['last_message_at'])
        except Message.DoesNotExist:
            pass 