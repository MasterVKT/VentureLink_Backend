"""
Modèles pour les commentaires génériques.
Ce système peut être utilisé pour commenter les projets, publications, etc.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from apps.core.models import TimeStampedModel, UUIDModel


class Comment(TimeStampedModel, UUIDModel):
    """
    Modèle générique pour les commentaires.
    Supporte les commentaires hiérarchiques (réponses à des commentaires).
    """
    # Relation générique - peut pointer vers n'importe quel modèle
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Type de contenu')
    )
    object_id = models.CharField(_('ID de l\'objet'), max_length=36)  # UUID as string
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Auteur du commentaire
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Auteur')
    )
    
    # Contenu du commentaire
    content = models.TextField(
        _('Contenu'),
        max_length=2000,
        help_text=_('Le contenu du commentaire (max 2000 caractères)')
    )
    
    # Support des commentaires hiérarchiques
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Commentaire parent')
    )
    
    # Statistiques
    likes_count = models.PositiveIntegerField(
        _('Nombre de likes'),
        default=0
    )
    replies_count = models.PositiveIntegerField(
        _('Nombre de réponses'),
        default=0
    )
    
    # Statut et modération
    is_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Indique si le commentaire est visible')
    )
    is_edited = models.BooleanField(
        _('Modifié'),
        default=False,
        help_text=_('Indique si le commentaire a été modifié')
    )
    edited_at = models.DateTimeField(
        _('Modifié le'),
        null=True,
        blank=True
    )
    
    # Modération
    is_flagged = models.BooleanField(
        _('Signalé'),
        default=False,
        help_text=_('Commentaire signalé par des utilisateurs')
    )
    flag_count = models.PositiveIntegerField(
        _('Nombre de signalements'),
        default=0
    )
    
    class Meta:
        verbose_name = _('commentaire')
        verbose_name_plural = _('commentaires')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.author.get_full_name()}: {content_preview}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Incrémenter le compteur de réponses du commentaire parent
        if is_new and self.parent:
            self.parent.replies_count += 1
            self.parent.save(update_fields=['replies_count'])
    
    def delete(self, *args, **kwargs):
        # Décrémenter le compteur de réponses du commentaire parent
        if self.parent:
            self.parent.replies_count -= 1
            self.parent.save(update_fields=['replies_count'])
        
        super().delete(*args, **kwargs)
    
    @property
    def depth(self):
        """
        Retourne la profondeur du commentaire dans la hiérarchie.
        """
        if not self.parent:
            return 0
        return self.parent.depth + 1
    
    @property
    def can_have_replies(self):
        """
        Limite la profondeur des réponses (par exemple, max 3 niveaux).
        """
        return self.depth < 3
    
    def get_thread_root(self):
        """
        Retourne le commentaire racine du thread.
        """
        if not self.parent:
            return self
        return self.parent.get_thread_root()
    
    def get_replies_tree(self):
        """
        Retourne les réponses organisées en arbre.
        """
        return Comment.objects.filter(
            parent=self,
            is_active=True
        ).prefetch_related('author', 'replies')


class CommentLike(TimeStampedModel, UUIDModel):
    """
    Modèle pour les likes sur les commentaires.
    """
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('Commentaire')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_likes',
        verbose_name=_('Utilisateur')
    )
    
    class Meta:
        verbose_name = _('like de commentaire')
        verbose_name_plural = _('likes de commentaires')
        unique_together = ('comment', 'user')
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} aime le commentaire de {self.comment.author.get_full_name()}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Incrémenter le compteur de likes du commentaire
        if is_new:
            self.comment.likes_count += 1
            self.comment.save(update_fields=['likes_count'])
    
    def delete(self, *args, **kwargs):
        # Décrémenter le compteur de likes du commentaire
        self.comment.likes_count -= 1
        self.comment.save(update_fields=['likes_count'])
        
        super().delete(*args, **kwargs) 