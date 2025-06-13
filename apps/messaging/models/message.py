"""
Models for message management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel
from apps.users.models import User
from apps.messaging.models.conversation import Conversation


class Message(UUIDModel, TimeStampedModel):
    """
    Model representing a message in a conversation.
    """
    STATUS_SENT = 'SENT'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_READ = 'READ'
    STATUS_FAILED = 'FAILED'
    STATUS_DELETED = 'DELETED'
    
    STATUS_CHOICES = [
        (STATUS_SENT, _('Envoyé')),
        (STATUS_DELIVERED, _('Livré')),
        (STATUS_READ, _('Lu')),
        (STATUS_FAILED, _('Échec')),
        (STATUS_DELETED, _('Supprimé')),
    ]
    
    TYPE_TEXT = 'TEXT'
    TYPE_IMAGE = 'IMAGE'
    TYPE_FILE = 'FILE'
    TYPE_AUDIO = 'AUDIO'
    TYPE_VIDEO = 'VIDEO'
    TYPE_LOCATION = 'LOCATION'
    TYPE_SYSTEM = 'SYSTEM'
    
    TYPE_CHOICES = [
        (TYPE_TEXT, _('Texte')),
        (TYPE_IMAGE, _('Image')),
        (TYPE_FILE, _('Fichier')),
        (TYPE_AUDIO, _('Audio')),
        (TYPE_VIDEO, _('Vidéo')),
        (TYPE_LOCATION, _('Localisation')),
        (TYPE_SYSTEM, _('Système')),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversation'),
    )
    
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        verbose_name=_('Expéditeur'),
    )
    
    message_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_TEXT,
    )
    
    content = models.TextField(
        _('Contenu'),
        help_text=_('Contenu du message (texte)'),
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SENT,
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Message parent'),
        help_text=_('Message auquel celui-ci répond')
    )
    
    is_system_message = models.BooleanField(
        _('Message système'),
        default=False,
        help_text=_('Indique si le message est généré par le système')
    )
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation']),
            models.Index(fields=['sender']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        if self.is_system_message:
            return f"[Système] {self.content[:50]}..."
        
        sender_name = self.sender.get_full_name() or self.sender.email if self.sender else "Inconnu"
        return f"{sender_name}: {self.content[:50]}..."


class MessageAttachment(UUIDModel, TimeStampedModel):
    """
    Model representing a file attachment in a message.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Message'),
    )
    
    file = models.FileField(
        _('Fichier'),
        upload_to='messages/attachments/%Y/%m/%d/',
        help_text=_('Fichier joint au message')
    )
    
    file_name = models.CharField(
        _('Nom du fichier'),
        max_length=255,
        help_text=_('Nom d\'origine du fichier')
    )
    
    file_size = models.PositiveIntegerField(
        _('Taille'),
        help_text=_('Taille du fichier en octets')
    )
    
    file_type = models.CharField(
        _('Type MIME'),
        max_length=100,
        help_text=_('Type MIME du fichier')
    )
    
    thumbnail = models.ImageField(
        _('Miniature'),
        upload_to='messages/thumbnails/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text=_('Miniature pour les images et vidéos')
    )
    
    class Meta:
        verbose_name = _('Pièce jointe')
        verbose_name_plural = _('Pièces jointes')
        indexes = [
            models.Index(fields=['message']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.get_file_size_display()})"
    
    def get_file_size_display(self):
        """
        Return a human-readable file size.
        """
        size = self.file_size
        
        if size < 1024:
            return f"{size} octets"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} Ko"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} Mo"
        else:
            return f"{size/(1024*1024*1024):.1f} Go"


class MessageRead(UUIDModel, TimeStampedModel):
    """
    Model tracking when messages are read by participants.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        verbose_name=_('Message'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_reads',
        verbose_name=_('Utilisateur'),
    )
    
    read_at = models.DateTimeField(
        _('Lu à'),
        auto_now_add=True,
        help_text=_('Date et heure de lecture du message')
    )
    
    class Meta:
        verbose_name = _('Accusé de lecture')
        verbose_name_plural = _('Accusés de lecture')
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        user_display = self.user.get_full_name() or self.user.email
        return f"{user_display} a lu le message {self.message.id}" 