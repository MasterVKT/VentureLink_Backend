"""
Admin configuration for messaging app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.messaging.models import (
    Conversation, ConversationParticipant,
    Message, MessageAttachment, MessageRead
)


class ConversationParticipantInline(admin.TabularInline):
    """
    Inline admin for conversation participants.
    """
    model = ConversationParticipant
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


class MessageInline(admin.TabularInline):
    """
    Inline admin for messages.
    """
    model = Message
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['sender', 'content', 'message_type', 'status', 'created_at']
    max_num = 10
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class MessageAttachmentInline(admin.TabularInline):
    """
    Inline admin for message attachments.
    """
    model = MessageAttachment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['file', 'file_name', 'file_size', 'file_type', 'thumbnail', 'created_at']
    max_num = 5


class MessageReadInline(admin.TabularInline):
    """
    Inline admin for message read receipts.
    """
    model = MessageRead
    extra = 0
    readonly_fields = ['read_at']
    fields = ['user', 'read_at']
    max_num = 10
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin interface for conversations.
    """
    list_display = ['id', 'title', 'conversation_type', 'project', 'status', 'participant_count', 'last_message_at', 'created_at']
    list_filter = ['conversation_type', 'status', 'created_at']
    search_fields = ['title', 'participants__email', 'participants__first_name', 'participants__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_message_at']
    inlines = [ConversationParticipantInline, MessageInline]
    
    def participant_count(self, obj):
        """
        Get the number of participants.
        """
        return obj.participants.count()
    participant_count.short_description = _('Nombre de participants')


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    """
    Admin interface for conversation participants.
    """
    list_display = ['id', 'conversation', 'user', 'is_admin', 'status', 'last_read_at', 'created_at']
    list_filter = ['is_admin', 'status', 'created_at']
    search_fields = ['conversation__title', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for messages.
    """
    list_display = ['id', 'conversation', 'sender', 'message_type', 'short_content', 'status', 'created_at']
    list_filter = ['message_type', 'status', 'created_at', 'is_system_message']
    search_fields = ['content', 'conversation__title', 'sender__email', 'sender__first_name', 'sender__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageAttachmentInline, MessageReadInline]
    
    def short_content(self, obj):
        """
        Get truncated content for display.
        """
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    short_content.short_description = _('Contenu')


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    """
    Admin interface for message attachments.
    """
    list_display = ['id', 'message', 'file_name', 'file_type', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['file_name', 'message__content', 'message__conversation__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def file_size_display(self, obj):
        """
        Get human-readable file size.
        """
        return obj.get_file_size_display()
    file_size_display.short_description = _('Taille') 