"""
Models initialization for the messaging app.
"""
from apps.messaging.models.conversation import (
    Conversation, ConversationParticipant
)
from apps.messaging.models.message import (
    Message, MessageAttachment, MessageRead
) 