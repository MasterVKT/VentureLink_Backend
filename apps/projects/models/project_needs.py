"""
Models for project needs and related functionalities.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.fields import MoneyField
from apps.projects.models.project import Project


class ProjectNeeds(UUIDModel, TimeStampedModel):
    """
    Model representing the funding and resource needs of a project.
    """
    RESOURCE_TYPE_INVESTMENT = 'INVESTMENT'
    RESOURCE_TYPE_LOAN = 'LOAN'
    RESOURCE_TYPE_PARTNERSHIP = 'PARTNERSHIP'
    RESOURCE_TYPE_EXPERTISE = 'EXPERTISE'
    RESOURCE_TYPE_MATERIAL = 'MATERIAL'
    
    RESOURCE_TYPE_CHOICES = [
        (RESOURCE_TYPE_INVESTMENT, _('Investissement')),
        (RESOURCE_TYPE_LOAN, _('Prêt')),
        (RESOURCE_TYPE_PARTNERSHIP, _('Partenariat')),
        (RESOURCE_TYPE_EXPERTISE, _('Expertise')),
        (RESOURCE_TYPE_MATERIAL, _('Matériel')),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='needs',
        verbose_name=_('Projet'),
    )
    
    resource_type = models.CharField(
        _('Type de ressource'),
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
    )
    
    title = models.CharField(
        _('Titre'),
        max_length=100,
    )
    
    description = models.TextField(
        _('Description'),
    )
    
    amount = MoneyField(
        _('Montant'),
        null=True,
        blank=True,
        help_text=_('Montant financier requis (si applicable)'),
    )
    
    is_critical = models.BooleanField(
        _('Critique'),
        default=False,
        help_text=_('Indique si ce besoin est critique pour le projet'),
    )
    
    deadline = models.DateField(
        _('Date limite'),
        null=True,
        blank=True,
        help_text=_('Date limite pour satisfaire ce besoin'),
    )
    
    is_satisfied = models.BooleanField(
        _('Satisfait'),
        default=False,
        help_text=_('Indique si ce besoin a été satisfait'),
    )
    
    class Meta:
        verbose_name = _('Besoin du projet')
        verbose_name_plural = _('Besoins du projet')
        ordering = ['is_satisfied', 'is_critical', '-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['is_critical']),
            models.Index(fields=['is_satisfied']),
        ]
    
    def __str__(self):
        return f"{self.project.title} - {self.title}"


class ProjectSkillsNeeded(UUIDModel, TimeStampedModel):
    """
    Model representing the skills needed for a project.
    """
    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, _('Faible')),
        (PRIORITY_MEDIUM, _('Moyenne')),
        (PRIORITY_HIGH, _('Haute')),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='skills_needed',
        verbose_name=_('Projet'),
    )
    
    name = models.CharField(
        _('Nom de la compétence'),
        max_length=100,
    )
    
    description = models.TextField(
        _('Description'),
        null=True,
        blank=True,
    )
    
    priority = models.CharField(
        _('Priorité'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )
    
    required_level = models.PositiveSmallIntegerField(
        _('Niveau requis'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Niveau requis de 1 (débutant) à 5 (expert)'),
        default=3,
    )
    
    is_satisfied = models.BooleanField(
        _('Satisfait'),
        default=False,
        help_text=_('Indique si ce besoin en compétence a été satisfait'),
    )
    
    class Meta:
        verbose_name = _('Compétence requise')
        verbose_name_plural = _('Compétences requises')
        ordering = ['is_satisfied', '-priority', 'name']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_satisfied']),
        ]
        unique_together = ['project', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_priority_display()})" 