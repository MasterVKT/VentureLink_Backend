"""
Models for project interactions such as interests, favorites, and comments.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel
from apps.users.models import User
from apps.projects.models.project import Project


class ProjectInterest(UUIDModel, TimeStampedModel):
    """
    Model representing a user's interest in a project.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_VIEWED = 'VIEWED'
    STATUS_CONTACTED = 'CONTACTED'
    STATUS_NEGOTIATING = 'NEGOTIATING'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('En attente')),
        (STATUS_VIEWED, _('Vu')),
        (STATUS_CONTACTED, _('Contacté')),
        (STATUS_NEGOTIATING, _('En négociation')),
        (STATUS_ACCEPTED, _('Accepté')),
        (STATUS_REJECTED, _('Refusé')),
        (STATUS_CANCELLED, _('Annulé')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_interests',
        verbose_name=_('Utilisateur'),
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='interests',
        verbose_name=_('Projet'),
    )
    
    message = models.TextField(
        _('Message'),
        help_text=_('Message de présentation ou d\'intérêt'),
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    
    is_anonymous = models.BooleanField(
        _('Anonyme'),
        default=False,
        help_text=_('Indique si l\'intérêt est exprimé de façon anonyme'),
    )
    
    investment_amount = models.DecimalField(
        _('Montant d\'investissement'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Montant que l\'utilisateur est prêt à investir'),
    )
    
    investment_currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    
    class Meta:
        verbose_name = _('Intérêt pour un projet')
        verbose_name_plural = _('Intérêts pour les projets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
            models.Index(fields=['status']),
        ]
        unique_together = ['user', 'project']
    
    def __str__(self):
        return f"{self.user.email} - {self.project.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Incrémenter le compteur d'intérêts si c'est une nouvelle entrée
        if is_new:
            self.project.interests_count += 1
            self.project.save(update_fields=['interests_count'])


class ProjectFavorite(UUIDModel, TimeStampedModel):
    """
    Model representing a user's favorite project.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_favorites',
        verbose_name=_('Utilisateur'),
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Projet'),
    )
    
    notes = models.TextField(
        _('Notes'),
        null=True,
        blank=True,
        help_text=_('Notes personnelles sur ce projet'),
    )
    
    class Meta:
        verbose_name = _('Projet favori')
        verbose_name_plural = _('Projets favoris')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
        ]
        unique_together = ['user', 'project']
    
    def __str__(self):
        return f"{self.user.email} - {self.project.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Incrémenter le compteur de favoris si c'est une nouvelle entrée
        if is_new:
            self.project.favorites_count += 1
            self.project.save(update_fields=['favorites_count'])


class ProjectQuestion(UUIDModel, TimeStampedModel):
    """
    Model representing questions asked about a project.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_questions',
        verbose_name=_('Utilisateur'),
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Projet'),
    )
    
    question = models.TextField(
        _('Question'),
    )
    
    is_public = models.BooleanField(
        _('Public'),
        default=True,
        help_text=_('Indique si la question est visible par tous les utilisateurs'),
    )
    
    is_answered = models.BooleanField(
        _('Répondu'),
        default=False,
        help_text=_('Indique si la question a reçu une réponse'),
    )
    
    class Meta:
        verbose_name = _('Question sur le projet')
        verbose_name_plural = _('Questions sur les projets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
            models.Index(fields=['is_public']),
            models.Index(fields=['is_answered']),
        ]
    
    def __str__(self):
        return f"Question de {self.user.email} sur {self.project.title}"


class ProjectQuestionAnswer(UUIDModel, TimeStampedModel):
    """
    Model representing answers to questions about a project.
    """
    question = models.OneToOneField(
        ProjectQuestion,
        on_delete=models.CASCADE,
        related_name='answer',
        verbose_name=_('Question'),
    )
    
    answered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_question_answers',
        verbose_name=_('Répondu par'),
    )
    
    answer = models.TextField(
        _('Réponse'),
    )
    
    class Meta:
        verbose_name = _('Réponse à une question')
        verbose_name_plural = _('Réponses aux questions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Réponse à la question de {self.question.user.email}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Mettre à jour le statut de la question
        if not self.question.is_answered:
            self.question.is_answered = True
            self.question.save(update_fields=['is_answered']) 