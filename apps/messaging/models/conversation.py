"""
Models for conversation management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel
from apps.users.models import User
from apps.projects.models import Project


class Conversation(UUIDModel, TimeStampedModel):
    """
    Model representing a conversation between two or more users.
    """
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_DELETED = 'DELETED'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Active')),
        (STATUS_ARCHIVED, _('Archivée')),
        (STATUS_DELETED, _('Supprimée')),
    ]
    
    TYPE_DIRECT = 'DIRECT'
    TYPE_PROJECT = 'PROJECT'
    TYPE_GROUP = 'GROUP'
    
    TYPE_CHOICES = [
        (TYPE_DIRECT, _('Message direct')),
        (TYPE_PROJECT, _('Discussion de projet')),
        (TYPE_GROUP, _('Groupe')),
    ]
    
    title = models.CharField(
        _('Titre'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Titre facultatif de la conversation (obligatoire pour les groupes)')
    )
    
    conversation_type = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_DIRECT,
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    
    participants = models.ManyToManyField(
        User,
        through='ConversationParticipant',
        related_name='conversations',
        verbose_name=_('Participants'),
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_('Projet associé'),
        help_text=_('Projet associé à la conversation, si applicable')
    )
    
    last_message_at = models.DateTimeField(
        _('Dernier message'),
        null=True,
        blank=True,
        help_text=_('Date et heure du dernier message')
    )
    
    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['conversation_type']),
            models.Index(fields=['status']),
            models.Index(fields=['last_message_at']),
        ]
    
    def __str__(self):
        if self.title:
            return self.title
        
        if self.conversation_type == self.TYPE_DIRECT:
            participants = self.participants.all()[:2]
            participant_names = [p.get_full_name() or p.email for p in participants]
            return f"Discussion: {' & '.join(participant_names)}"
        
        if self.conversation_type == self.TYPE_PROJECT and self.project:
            return f"Projet: {self.project.title}"
        
        return f"Conversation {self.id}"


class ConversationParticipant(UUIDModel, TimeStampedModel):
    """
    Model representing a participant in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='conversation_participants',
        verbose_name=_('Conversation'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversation_participations',
        verbose_name=_('Utilisateur'),
    )
    
    is_admin = models.BooleanField(
        _('Administrateur'),
        default=False,
        help_text=_('Indique si l\'utilisateur est administrateur de la conversation')
    )
    
    last_read_at = models.DateTimeField(
        _('Dernière lecture'),
        null=True,
        blank=True,
        help_text=_('Date et heure de la dernière lecture des messages')
    )
    
    nickname = models.CharField(
        _('Surnom'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Surnom personnalisé pour l\'utilisateur dans cette conversation')
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=Conversation.STATUS_CHOICES,
        default=Conversation.STATUS_ACTIVE,
        help_text=_('Statut de l\'utilisateur dans cette conversation')
    )
    
    muted_until = models.DateTimeField(
        _('Muet jusqu\'à'),
        null=True,
        blank=True,
        help_text=_('Date et heure jusqu\'à laquelle la conversation est mise en sourdine')
    )
    
    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['conversation', 'user']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        user_display = self.user.get_full_name() or self.user.email
        return f"{user_display} - {self.conversation}" 