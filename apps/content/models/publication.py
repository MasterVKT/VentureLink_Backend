"""
Modèles pour les publications administratives.
Les publications sont créées uniquement par les administrateurs et peuvent être de différents types.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxValueValidator

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.utils import get_file_path


def publication_media_upload_path(instance, filename):
    """
    Function to determine the upload path for publication media files.
    """
    return get_file_path(instance, filename, 'publications/media')


class Publication(TimeStampedModel, UUIDModel):
    """
    Modèle pour les publications administratives.
    Ces publications sont créées par les administrateurs et servent à informer,
    éduquer ou divertir la communauté.
    """
    
    # Types de publications
    TYPE_EDUCATIONAL = 'EDUCATIONAL'
    TYPE_ENTERTAINING = 'ENTERTAINING'
    TYPE_MOTIVATIONAL = 'MOTIVATIONAL'
    TYPE_INFORMATIONAL = 'INFORMATIONAL'
    TYPE_TIPS = 'TIPS'
    TYPE_ADVERTISING = 'ADVERTISING'
    TYPE_SPONSORED = 'SPONSORED'
    TYPE_NEWS = 'NEWS'
    TYPE_TUTORIAL = 'TUTORIAL'
    TYPE_CASE_STUDY = 'CASE_STUDY'
    
    TYPE_CHOICES = [
        (TYPE_EDUCATIONAL, _('Éducatif')),
        (TYPE_ENTERTAINING, _('Divertissant')),
        (TYPE_MOTIVATIONAL, _('Motivant')),
        (TYPE_INFORMATIONAL, _('Informatif')),
        (TYPE_TIPS, _('Conseils')),
        (TYPE_ADVERTISING, _('Publicitaire')),
        (TYPE_SPONSORED, _('Sponsorisé')),
        (TYPE_NEWS, _('Actualités')),
        (TYPE_TUTORIAL, _('Tutoriel')),
        (TYPE_CASE_STUDY, _('Étude de cas')),
    ]
    
    # Domaines
    DOMAIN_PROJECT_MANAGEMENT = 'PROJECT_MANAGEMENT'
    DOMAIN_FINANCE_INVESTMENT = 'FINANCE_INVESTMENT'
    DOMAIN_ENTREPRENEURSHIP = 'ENTREPRENEURSHIP'
    DOMAIN_PERSONAL_DEVELOPMENT = 'PERSONAL_DEVELOPMENT'
    DOMAIN_MARKETING_COMMUNICATION = 'MARKETING_COMMUNICATION'
    DOMAIN_TECHNOLOGY = 'TECHNOLOGY'
    DOMAIN_BUSINESS_STRATEGY = 'BUSINESS_STRATEGY'
    DOMAIN_LEADERSHIP = 'LEADERSHIP'
    DOMAIN_INNOVATION = 'INNOVATION'
    DOMAIN_NETWORKING = 'NETWORKING'
    
    DOMAIN_CHOICES = [
        (DOMAIN_PROJECT_MANAGEMENT, _('Gestion de projets')),
        (DOMAIN_FINANCE_INVESTMENT, _('Finances et investissements')),
        (DOMAIN_ENTREPRENEURSHIP, _('Entrepreneuriat')),
        (DOMAIN_PERSONAL_DEVELOPMENT, _('Développement personnel')),
        (DOMAIN_MARKETING_COMMUNICATION, _('Marketing et communication')),
        (DOMAIN_TECHNOLOGY, _('Technologie')),
        (DOMAIN_BUSINESS_STRATEGY, _('Stratégie d\'entreprise')),
        (DOMAIN_LEADERSHIP, _('Leadership')),
        (DOMAIN_INNOVATION, _('Innovation')),
        (DOMAIN_NETWORKING, _('Réseautage')),
    ]
    
    # Statuts
    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_SCHEDULED = 'SCHEDULED'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Brouillon')),
        (STATUS_PUBLISHED, _('Publié')),
        (STATUS_ARCHIVED, _('Archivé')),
        (STATUS_SCHEDULED, _('Programmé')),
    ]
    
    # Informations de base
    title = models.CharField(
        _('Titre'),
        max_length=200,
        validators=[MinLengthValidator(10)],
        help_text=_('Titre de la publication (10-200 caractères)')
    )
    
    content = models.TextField(
        _('Contenu'),
        validators=[MinLengthValidator(50)],
        help_text=_('Contenu principal de la publication')
    )
    
    summary = models.CharField(
        _('Résumé'),
        max_length=300,
        blank=True,
        null=True,
        help_text=_('Résumé court de la publication pour l\'aperçu')
    )
    
    # Classification
    publication_type = models.CharField(
        _('Type de publication'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_INFORMATIONAL
    )
    
    domain = models.CharField(
        _('Domaine'),
        max_length=30,
        choices=DOMAIN_CHOICES,
        default=DOMAIN_ENTREPRENEURSHIP
    )
    
    tags = models.CharField(
        _('Tags'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Tags séparés par des virgules')
    )
    
    # Métadonnées
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='authored_publications',
        verbose_name=_('Auteur'),
        limit_choices_to={'is_staff': True}
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    
    # Dates importantes
    published_at = models.DateTimeField(
        _('Date de publication'),
        null=True,
        blank=True,
        help_text=_('Date et heure de publication')
    )
    
    scheduled_for = models.DateTimeField(
        _('Programmé pour'),
        null=True,
        blank=True,
        help_text=_('Date et heure de publication programmée')
    )
    
    # Statistiques
    views_count = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0
    )
    
    likes_count = models.PositiveIntegerField(
        _('Nombre de likes'),
        default=0
    )
    
    comments_count = models.PositiveIntegerField(
        _('Nombre de commentaires'),
        default=0
    )
    
    shares_count = models.PositiveIntegerField(
        _('Nombre de partages'),
        default=0
    )
    
    # Paramètres d'affichage
    is_featured = models.BooleanField(
        _('Mise en avant'),
        default=False,
        help_text=_('Publication mise en avant sur la page d\'accueil')
    )
    
    is_pinned = models.BooleanField(
        _('Épinglé'),
        default=False,
        help_text=_('Publication épinglée en haut du fil')
    )
    
    allow_comments = models.BooleanField(
        _('Autoriser les commentaires'),
        default=True,
        help_text=_('Permet aux utilisateurs de commenter cette publication')
    )
    
    # Informations de sponsoring/publicité
    is_sponsored = models.BooleanField(
        _('Contenu sponsorisé'),
        default=False,
        help_text=_('Indique si c\'est un contenu sponsorisé')
    )
    
    sponsor_name = models.CharField(
        _('Nom du sponsor'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nom de l\'entreprise ou organisation sponsor')
    )
    
    sponsor_url = models.URLField(
        _('URL du sponsor'),
        blank=True,
        null=True,
        help_text=_('Site web du sponsor')
    )
    
    # Champs SEO
    meta_description = models.CharField(
        _('Meta description'),
        max_length=160,
        blank=True,
        null=True,
        help_text=_('Description pour les moteurs de recherche')
    )
    
    slug = models.SlugField(
        _('Slug'),
        max_length=250,
        unique=True,
        blank=True,
        null=True,
        help_text=_('URL slug pour la publication')
    )
    
    # Relation générique pour les commentaires
    comments = GenericRelation(
        'content.Comment',
        content_type_field='content_type',
        object_id_field='object_id'
    )
    
    class Meta:
        verbose_name = _('publication')
        verbose_name_plural = _('publications')
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['status']),
            models.Index(fields=['publication_type']),
            models.Index(fields=['domain']),
            models.Index(fields=['published_at']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_pinned']),
            models.Index(fields=['is_sponsored']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le slug si pas fourni
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(self.title)[:200]
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        
        # Mettre à jour la date de publication si le statut change vers PUBLISHED
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        """Vérifie si la publication est publiée."""
        return self.status == self.STATUS_PUBLISHED and self.published_at
    
    @property
    def can_be_commented(self):
        """Vérifie si la publication peut être commentée."""
        return self.allow_comments and self.is_published
    
    def get_tags_list(self):
        """Retourne la liste des tags."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_views(self):
        """Incrémente le compteur de vues."""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class PublicationMedia(TimeStampedModel, UUIDModel):
    """
    Modèle pour les médias des publications (images, vidéos, documents).
    Maximum 3 médias par publication.
    """
    MEDIA_TYPE_IMAGE = 'IMAGE'
    MEDIA_TYPE_VIDEO = 'VIDEO'
    MEDIA_TYPE_DOCUMENT = 'DOCUMENT'
    MEDIA_TYPE_AUDIO = 'AUDIO'
    
    MEDIA_TYPE_CHOICES = [
        (MEDIA_TYPE_IMAGE, _('Image')),
        (MEDIA_TYPE_VIDEO, _('Vidéo')),
        (MEDIA_TYPE_DOCUMENT, _('Document')),
        (MEDIA_TYPE_AUDIO, _('Audio')),
    ]
    
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name=_('Publication')
    )
    
    file = models.FileField(
        _('Fichier'),
        upload_to=publication_media_upload_path,
        help_text=_('Fichier média (image, vidéo, document, audio)')
    )
    
    media_type = models.CharField(
        _('Type de média'),
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        default=MEDIA_TYPE_IMAGE
    )
    
    title = models.CharField(
        _('Titre'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Titre du média')
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        null=True,
        help_text=_('Description du média')
    )
    
    alt_text = models.CharField(
        _('Texte alternatif'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Texte alternatif pour l\'accessibilité')
    )
    
    order = models.PositiveSmallIntegerField(
        _('Ordre'),
        default=0,
        validators=[MaxValueValidator(2)],
        help_text=_('Ordre d\'affichage (0, 1, 2)')
    )
    
    is_featured = models.BooleanField(
        _('Image de couverture'),
        default=False,
        help_text=_('Image utilisée comme couverture de la publication')
    )
    
    file_size = models.PositiveIntegerField(
        _('Taille du fichier'),
        null=True,
        blank=True,
        help_text=_('Taille du fichier en octets')
    )
    
    class Meta:
        verbose_name = _('média de publication')
        verbose_name_plural = _('médias de publication')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['publication']),
            models.Index(fields=['media_type']),
            models.Index(fields=['is_featured']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(order__lte=2),
                name='publication_media_max_3'
            )
        ]
    
    def __str__(self):
        return f"{self.publication.title} - {self.get_media_type_display()} {self.order + 1}"
    
    def save(self, *args, **kwargs):
        # Calculer la taille du fichier
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        
        # Si ce média est défini comme featured, désactiver ce statut pour les autres
        if self.is_featured:
            PublicationMedia.objects.filter(
                publication=self.publication,
                is_featured=True
            ).exclude(id=self.id).update(is_featured=False)
        
        super().save(*args, **kwargs)


class PublicationLike(TimeStampedModel, UUIDModel):
    """
    Modèle pour les likes sur les publications.
    """
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('Publication')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='publication_likes',
        verbose_name=_('Utilisateur')
    )
    
    class Meta:
        verbose_name = _('like de publication')
        verbose_name_plural = _('likes de publication')
        unique_together = ('publication', 'user')
        indexes = [
            models.Index(fields=['publication']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} aime {self.publication.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Incrémenter le compteur de likes de la publication
        if is_new:
            self.publication.likes_count += 1
            self.publication.save(update_fields=['likes_count'])
    
    def delete(self, *args, **kwargs):
        # Décrémenter le compteur de likes de la publication
        self.publication.likes_count -= 1
        self.publication.save(update_fields=['likes_count'])
        
        super().delete(*args, **kwargs) 