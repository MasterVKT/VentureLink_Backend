from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.utils import get_file_path
from apps.users.validators import (
    linkedin_validator, twitter_validator, facebook_validator,
    min_years_validator, max_years_validator, education_year_validator,
    validate_experience_dates, validate_education_dates, validate_color_code
)


def profile_picture_upload_path(instance, filename):
    """
    Function to determine the upload path for profile pictures.
    """
    return get_file_path(instance, filename, 'profile_pictures')


def cover_picture_upload_path(instance, filename):
    """
    Function to determine the upload path for cover pictures.
    """
    return get_file_path(instance, filename, 'cover_pictures')


class Profile(TimeStampedModel, UUIDModel):
    """
    Modèle pour les profils d'utilisateurs, contenant des informations détaillées.
    """
    VERIFICATION_LEVEL_CHOICES = (
        ('BASIC', _('Basique')),
        ('ADVANCED', _('Avancé')),
        ('VERIFIED', _('Vérifié')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Utilisateur')
    )
    
    # Photo et image de couverture
    profile_picture = models.ImageField(
        _('Photo de profil'),
        upload_to=profile_picture_upload_path,
        blank=True,
        null=True
    )
    cover_picture = models.ImageField(
        _('Image de couverture'),
        upload_to=cover_picture_upload_path,
        blank=True,
        null=True
    )
    
    # Informations professionnelles
    bio_short = models.CharField(_('Bio courte'), max_length=280, blank=True, null=True)
    title = models.CharField(_('Titre professionnel'), max_length=100, blank=True, null=True)
    website = models.URLField(_('Site web'), max_length=200, blank=True, null=True)
    
    # Réseaux sociaux
    social_linkedin = models.URLField(
        _('LinkedIn'),
        max_length=200,
        blank=True,
        null=True,
        validators=[linkedin_validator]
    )
    social_twitter = models.URLField(
        _('Twitter'),
        max_length=200,
        blank=True,
        null=True,
        validators=[twitter_validator]
    )
    social_facebook = models.URLField(
        _('Facebook'),
        max_length=200,
        blank=True,
        null=True,
        validators=[facebook_validator]
    )
    
    # Statistiques
    views_count = models.PositiveIntegerField(_('Nombre de vues'), default=0)
    avg_rating = models.DecimalField(_('Note moyenne'), max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(_('Nombre d\'évaluations'), default=0)
    
    # Niveau de vérification
    verification_level = models.CharField(
        _('Niveau de vérification'),
        max_length=20,
        choices=VERIFICATION_LEVEL_CHOICES,
        default='BASIC'
    )
    
    class Meta:
        verbose_name = _('profil')
        verbose_name_plural = _('profils')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profil de {self.user.email}"
    
    def increment_views(self):
        """
        Incrémente le compteur de vues.
        """
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def update_rating(self, new_rating):
        """
        Met à jour la note moyenne avec une nouvelle évaluation.
        
        Args:
            new_rating (Decimal): La nouvelle note à ajouter
        """
        if self.rating_count == 0:
            self.avg_rating = new_rating
        else:
            # Calculer la nouvelle moyenne
            total = self.avg_rating * self.rating_count
            self.avg_rating = (total + new_rating) / (self.rating_count + 1)
        
        self.rating_count += 1
        self.save(update_fields=['avg_rating', 'rating_count'])


class DomainExpertise(TimeStampedModel, UUIDModel):
    """
    Modèle pour les domaines d'expertise d'un utilisateur.
    """
    LEVEL_CHOICES = (
        ('BEGINNER', _('Débutant')),
        ('INTERMEDIATE', _('Intermédiaire')),
        ('EXPERT', _('Expert')),
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='domain_expertise',
        verbose_name=_('Profil')
    )
    name = models.CharField(_('Nom du domaine'), max_length=100)
    years_experience = models.PositiveSmallIntegerField(
        _('Années d\'expérience'),
        blank=True,
        null=True,
        validators=[min_years_validator, max_years_validator]
    )
    level = models.CharField(
        _('Niveau d\'expertise'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='INTERMEDIATE'
    )
    
    class Meta:
        verbose_name = _('expertise')
        verbose_name_plural = _('expertises')
        ordering = ['-level', 'name']
        unique_together = ('profile', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class ProjectInterest(TimeStampedModel, UUIDModel):
    """
    Modèle pour les centres d'intérêt d'un utilisateur en matière de projets.
    """
    LEVEL_CHOICES = (
        ('LOW', _('Faible')),
        ('MEDIUM', _('Moyen')),
        ('HIGH', _('Élevé')),
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='project_interests',
        verbose_name=_('Profil')
    )
    name = models.CharField(_('Nom de l\'intérêt'), max_length=100)
    level = models.CharField(
        _('Niveau d\'intérêt'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='MEDIUM'
    )
    
    class Meta:
        verbose_name = _('intérêt de projet')
        verbose_name_plural = _('intérêts de projets')
        ordering = ['-level', 'name']
        unique_together = ('profile', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Education(TimeStampedModel, UUIDModel):
    """
    Modèle pour les formations d'un utilisateur.
    """
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='education',
        verbose_name=_('Profil')
    )
    institution = models.CharField(_('Établissement'), max_length=200)
    degree = models.CharField(_('Diplôme'), max_length=200)
    field_of_study = models.CharField(_('Domaine d\'étude'), max_length=200, blank=True, null=True)
    start_year = models.CharField(
        _('Année de début'),
        max_length=4,
        validators=[education_year_validator]
    )
    end_year = models.CharField(
        _('Année de fin'),
        max_length=4,
        blank=True,
        null=True,
        validators=[education_year_validator]
    )
    description = models.TextField(_('Description'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('formation')
        verbose_name_plural = _('formations')
        ordering = ['-end_year', '-start_year']
    
    def __str__(self):
        return f"{self.degree} - {self.institution} ({self.start_year})"
    
    def clean(self):
        """
        Validation personnalisée pour les dates de formation.
        """
        super().clean()
        
        if self.start_year and self.end_year:
            validate_education_dates(self.start_year, self.end_year)


class Experience(TimeStampedModel, UUIDModel):
    """
    Modèle pour les expériences professionnelles d'un utilisateur.
    """
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='experience',
        verbose_name=_('Profil')
    )
    company = models.CharField(_('Entreprise'), max_length=200)
    title = models.CharField(_('Poste'), max_length=200)
    location = models.CharField(_('Lieu'), max_length=200, blank=True, null=True)
    current = models.BooleanField(_('Poste actuel'), default=False)
    start_date = models.CharField(_('Date de début'), max_length=7)  # Format: YYYY-MM
    end_date = models.CharField(_('Date de fin'), max_length=7, blank=True, null=True)  # Format: YYYY-MM
    description = models.TextField(_('Description'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('expérience')
        verbose_name_plural = _('expériences')
        ordering = ['-current', '-end_date', '-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.company}"
    
    def clean(self):
        """
        Validation personnalisée pour les dates d'expérience.
        """
        super().clean()
        
        validate_experience_dates(self.start_date, self.end_date, self.current)


class Badge(TimeStampedModel, UUIDModel):
    """
    Modèle pour les badges des utilisateurs.
    """
    BADGE_TYPE_CHOICES = (
        ('VERIFICATION', _('Vérification')),
        ('ACHIEVEMENT', _('Réalisation')),
        ('SPECIAL', _('Spécial')),
    )
    
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'))
    badge_type = models.CharField(
        _('Type de badge'),
        max_length=20,
        choices=BADGE_TYPE_CHOICES,
        default='ACHIEVEMENT'
    )
    color = models.CharField(
        _('Couleur'),
        max_length=7,
        default='#42B72A',
        validators=[validate_color_code]
    )  # Format: #RRGGBB
    icon = models.CharField(_('Icône'), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('badge')
        verbose_name_plural = _('badges')
        ordering = ['badge_type', 'name']
    
    def __str__(self):
        return self.name


class UserBadge(TimeStampedModel, UUIDModel):
    """
    Modèle associant des badges aux utilisateurs.
    """
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_('Profil')
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='user_badges',
        verbose_name=_('Badge')
    )
    
    class Meta:
        verbose_name = _('badge utilisateur')
        verbose_name_plural = _('badges utilisateurs')
        unique_together = ('profile', 'badge')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.badge.name} - {self.profile.user.email}" 