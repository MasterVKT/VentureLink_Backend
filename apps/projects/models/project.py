"""
Models for project categories, tags and projects.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDModel
from apps.users.models import User


class ProjectCategory(UUIDModel, TimeStampedModel):
    """
    Model representing a category for projects.
    Categories are used to classify projects.
    """
    name_fr = models.CharField(
        _('Nom (FR)'),
        max_length=100,
    )
    name_en = models.CharField(
        _('Nom (EN)'),
        max_length=100,
    )
    icon = models.CharField(
        _('Icône'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Nom de l\'icône dans la bibliothèque d\'icônes')
    )
    description_fr = models.TextField(
        _('Description (FR)'),
        null=True,
        blank=True,
    )
    description_en = models.TextField(
        _('Description (EN)'),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )

    class Meta:
        verbose_name = _('Catégorie de projet')
        verbose_name_plural = _('Catégories de projets')
        ordering = ['name_fr']

    def __str__(self):
        return self.name_fr


class ProjectTag(UUIDModel, TimeStampedModel):
    """
    Model representing a tag for projects.
    Tags are used to label projects with specific keywords.
    """
    name_fr = models.CharField(
        _('Nom (FR)'),
        max_length=50,
    )
    name_en = models.CharField(
        _('Nom (EN)'),
        max_length=50,
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )

    class Meta:
        verbose_name = _('Tag de projet')
        verbose_name_plural = _('Tags de projets')
        ordering = ['name_fr']

    def __str__(self):
        return self.name_fr


class Project(UUIDModel, TimeStampedModel):
    """
    Model representing a project.
    Projects are created by users to present their business ideas
    and find investors or partners.
    """
    STAGE_IDEA = 'IDEA'
    STAGE_PROTOTYPE = 'PROTOTYPE'
    STAGE_DEVELOPMENT = 'DEVELOPMENT'
    STAGE_GROWTH = 'GROWTH'
    
    STAGE_CHOICES = [
        (STAGE_IDEA, _('Idée')),
        (STAGE_PROTOTYPE, _('Prototype')),
        (STAGE_DEVELOPMENT, _('En développement')),
        (STAGE_GROWTH, _('En phase de croissance')),
    ]
    
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_INACTIVE = 'INACTIVE'
    STATUS_FUNDED = 'FUNDED'
    STATUS_ARCHIVED = 'ARCHIVED'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Actif')),
        (STATUS_INACTIVE, _('Inactif')),
        (STATUS_FUNDED, _('Financé')),
        (STATUS_ARCHIVED, _('Archivé')),
    ]
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_projects',
        verbose_name=_('Créateur'),
    )
    title = models.CharField(
        _('Titre'),
        max_length=100,
        validators=[MinLengthValidator(10)],
    )
    short_description = models.CharField(
        _('Description courte'),
        max_length=280,
        validators=[MinLengthValidator(20)],
    )
    full_description = models.TextField(
        _('Description complète'),
        validators=[MinLengthValidator(100)],
    )
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        related_name='projects',
        verbose_name=_('Catégorie'),
    )
    stage = models.CharField(
        _('Stade'),
        max_length=20,
        choices=STAGE_CHOICES,
        default=STAGE_IDEA,
    )
    funding_min = models.DecimalField(
        _('Financement minimum'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    funding_max = models.DecimalField(
        _('Financement maximum'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    funding_currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    location_country = models.CharField(
        _('Pays'),
        max_length=100,
        null=True,
        blank=True,
    )
    location_city = models.CharField(
        _('Ville'),
        max_length=100,
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        ProjectTag,
        related_name='projects',
        verbose_name=_('Tags'),
        blank=True,
    )
    is_premium = models.BooleanField(
        _('Premium'),
        default=False,
        help_text=_('Projet avec fonctionnalités premium'),
    )
    is_featured = models.BooleanField(
        _('Mis en avant'),
        default=False,
        help_text=_('Projet mis en avant sur la page d\'accueil'),
    )
    is_draft = models.BooleanField(
        _('Brouillon'),
        default=True,
        help_text=_('Projet en cours d\'édition, non publié'),
    )
    
    # Système de vérification
    is_verified = models.BooleanField(
        _('Vérifié'),
        default=False,
        help_text=_('Projet vérifié et validé par l\'équipe administrative'),
    )
    verified_at = models.DateTimeField(
        _('Date de vérification'),
        null=True,
        blank=True,
        help_text=_('Date à laquelle le projet a été vérifié'),
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_projects',
        verbose_name=_('Vérifié par'),
        help_text=_('Administrateur qui a vérifié le projet'),
    )
    verification_notes = models.TextField(
        _('Notes de vérification'),
        blank=True,
        help_text=_('Notes internes sur la vérification (visible uniquement aux administrateurs)'),
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    views_count = models.PositiveIntegerField(
        _('Nombre de vues'),
        default=0,
    )
    interests_count = models.PositiveIntegerField(
        _('Nombre d\'intérêts'),
        default=0,
    )
    favorites_count = models.PositiveIntegerField(
        _('Nombre de favoris'),
        default=0,
    )
    comments_count = models.PositiveIntegerField(
        _('Nombre de commentaires'),
        default=0,
    )
    published_at = models.DateTimeField(
        _('Date de publication'),
        null=True,
        blank=True,
    )
    business_plan = models.FileField(
        _('Business plan'),
        upload_to='projects/business_plans/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('Fichier PDF du business plan (Premium uniquement)'),
    )
    video_url = models.URLField(
        _('URL vidéo'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('URL d\'une vidéo de présentation (YouTube, Vimeo, etc.)'),
    )
    
    # Relation générique pour les commentaires
    comments = GenericRelation(
        'content.Comment',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='project'
    )

    class Meta:
        verbose_name = _('Projet')
        verbose_name_plural = _('Projets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator']),
            models.Index(fields=['category']),
            models.Index(fields=['stage']),
            models.Index(fields=['status']),
            models.Index(fields=['is_draft']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['published_at']),
            models.Index(fields=['verified_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Validate funding_min and funding_max
        if self.funding_min and self.funding_max and self.funding_min > self.funding_max:
            raise ValueError(_('Le financement minimum ne peut pas être supérieur au financement maximum'))
        super().save(*args, **kwargs)
        
    @property
    def primary_image(self):
        """Return the primary image for this project or None if no image exists."""
        return self.media.filter(is_primary=True).first()
        
    def has_premium_features(self):
        """Check if the project should have premium features enabled."""
        return self.is_premium or (self.creator and self.creator.is_premium)

    @property
    def is_published(self):
        """
        Un projet est considéré comme publié s'il n'est pas un brouillon et que son statut est ACTIF.
        """
        return not self.is_draft and self.status == self.STATUS_ACTIVE
    
    @property
    def can_be_commented(self):
        """
        Un projet peut être commenté s'il est publié.
        """
        return self.is_published
    
    def verify_project(self, verified_by_user, notes=""):
        """
        Marque le projet comme vérifié par un administrateur.
        
        Args:
            verified_by_user (User): L'utilisateur administrateur qui effectue la vérification
            notes (str): Notes optionnelles sur la vérification
        """
        if not verified_by_user.is_staff:
            raise ValueError(_('Seuls les administrateurs peuvent vérifier des projets'))
        
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verified_by = verified_by_user
        self.verification_notes = notes
        self.save()
    
    def unverify_project(self, unverified_by_user, notes=""):
        """
        Retire la vérification d'un projet.
        
        Args:
            unverified_by_user (User): L'utilisateur administrateur qui retire la vérification
            notes (str): Notes optionnelles sur le retrait de vérification
        """
        if not unverified_by_user.is_staff:
            raise ValueError(_('Seuls les administrateurs peuvent retirer la vérification des projets'))
        
        self.is_verified = False
        self.verified_at = None
        self.verified_by = None
        self.verification_notes = f"Vérification retirée le {timezone.now().strftime('%d/%m/%Y à %H:%M')} par {unverified_by_user.get_full_name()}. {notes}"
        self.save()
    
    @property
    def verification_status_display(self):
        """
        Retourne le statut de vérification formaté pour l'affichage.
        """
        if self.is_verified:
            return _('Vérifié le {}').format(
                self.verified_at.strftime('%d/%m/%Y') if self.verified_at else _('Date inconnue')
            )
        return _('Non vérifié') 