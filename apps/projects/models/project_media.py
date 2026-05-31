"""
Models for project media and related functionalities.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.utils import get_file_path
from apps.projects.models.project import Project


def project_media_upload_path(instance, filename):
    """
    Function to determine the upload path for project media files.
    """
    return get_file_path(instance, filename, 'projects/media')


class ProjectMedia(UUIDModel, TimeStampedModel):
    """
    Model representing media files (images, videos, documents) for a project.
    """
    MEDIA_TYPE_IMAGE = 'IMAGE'
    MEDIA_TYPE_VIDEO = 'VIDEO'
    MEDIA_TYPE_DOCUMENT = 'DOCUMENT'

    MEDIA_TYPE_CHOICES = [
        (MEDIA_TYPE_IMAGE, _('Image')),
        (MEDIA_TYPE_VIDEO, _('Vidéo')),
        (MEDIA_TYPE_DOCUMENT, _('Document')),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name=_('Projet'),
    )

    file = models.FileField(
        _('Fichier'),
        upload_to=project_media_upload_path,
    )

    media_type = models.CharField(
        _('Type de média'),
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        default=MEDIA_TYPE_IMAGE,
    )

    title = models.CharField(
        _('Titre'),
        max_length=100,
        null=True,
        blank=True,
    )

    description = models.TextField(
        _('Description'),
        null=True,
        blank=True,
    )

    is_primary = models.BooleanField(
        _('Image principale'),
        default=False,
        help_text=_('Indique si cette image est l\'image principale du projet'),
    )

    order = models.PositiveSmallIntegerField(
        _('Ordre'),
        default=0,
        help_text=_('Ordre d\'affichage du média'),
    )

    size = models.PositiveIntegerField(
        _('Taille en bytes'),
        null=True,
        blank=True,
        help_text=_('Taille du fichier en bytes'),
    )

    uploader = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_media',
        verbose_name=_('Téléchargeur'),
    )

    class Meta:
        verbose_name = _('Média du projet')
        verbose_name_plural = _('Médias du projet')
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['media_type']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['uploader']),
        ]

    def __str__(self):
        return f"{self.project.title} - {self.get_media_type_display()} - {self.id}"

    def save(self, *args, **kwargs):
        # Si ce média est défini comme principal, désactiver ce statut pour les autres médias
        if self.is_primary:
            ProjectMedia.objects.filter(
                project=self.project,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

        super().save(*args, **kwargs)