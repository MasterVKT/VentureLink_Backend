from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.utils import get_file_path


def company_logo_upload_path(instance, filename):
    """
    Function to determine the upload path for company logos.
    """
    return get_file_path(instance, filename, 'company_logos')


class CompanyProfile(TimeStampedModel, UUIDModel):
    """
    Modèle pour les profils d'entreprise, contenant des informations spécifiques aux sociétés.
    """
    COMPANY_SIZE_CHOICES = (
        ('STARTUP', _('Startup (1-10 employés)')),
        ('SMALL', _('Petite entreprise (11-50 employés)')),
        ('MEDIUM', _('Entreprise moyenne (51-250 employés)')),
        ('LARGE', _('Grande entreprise (250+ employés)')),
    )
    
    COMPANY_STAGE_CHOICES = (
        ('IDEA', _('Idée')),
        ('PROTOTYPE', _('Prototype')),
        ('MVP', _('MVP')),
        ('EARLY_STAGE', _('Stade précoce')),
        ('GROWTH', _('Croissance')),
        ('MATURE', _('Maturité')),
    )
    
    LEGAL_FORM_CHOICES = (
        ('SARL', _('SARL')),
        ('SAS', _('SAS')),
        ('SA', _('SA')),
        ('SNC', _('SNC')),
        ('EURL', _('EURL')),
        ('SASU', _('SASU')),
        ('EI', _('Entreprise Individuelle')),
        ('EIRL', _('EIRL')),
        ('AUTO_ENTREPRENEUR', _('Auto-entrepreneur')),
        ('ASSOCIATION', _('Association')),
        ('OTHER', _('Autre')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_profile',
        verbose_name=_('Utilisateur'),
        limit_choices_to={'account_type': 'BUSINESS'}
    )
    
    # Informations de base de l'entreprise
    company_name = models.CharField(_('Nom de l\'entreprise'), max_length=200)
    legal_name = models.CharField(_('Raison sociale'), max_length=200, blank=True, null=True)
    registration_number = models.CharField(
        _('Numéro d\'enregistrement'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('SIRET, RCS, etc.')
    )
    vat_number = models.CharField(
        _('Numéro de TVA'),
        max_length=50,
        blank=True,
        null=True
    )
    legal_form = models.CharField(
        _('Forme juridique'),
        max_length=30,
        choices=LEGAL_FORM_CHOICES,
        blank=True,
        null=True
    )
    
    # Logo et informations visuelles
    logo = models.ImageField(
        _('Logo de l\'entreprise'),
        upload_to=company_logo_upload_path,
        blank=True,
        null=True
    )
    
    # Informations descriptives
    description = models.TextField(_('Description de l\'entreprise'), max_length=2000, blank=True, null=True)
    mission_statement = models.TextField(_('Mission'), max_length=500, blank=True, null=True)
    industry = models.CharField(_('Secteur d\'activité'), max_length=100, blank=True, null=True)
    specialties = models.TextField(_('Spécialités'), max_length=500, blank=True, null=True)
    
    # Informations sur la taille et le stade
    company_size = models.CharField(
        _('Taille de l\'entreprise'),
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True,
        null=True
    )
    employee_count = models.PositiveIntegerField(
        _('Nombre d\'employés'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )
    company_stage = models.CharField(
        _('Stade de l\'entreprise'),
        max_length=20,
        choices=COMPANY_STAGE_CHOICES,
        blank=True,
        null=True
    )
    founded_year = models.PositiveIntegerField(
        _('Année de création'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1800), MaxValueValidator(2030)]
    )
    
    # Informations de contact
    headquarters_address = models.TextField(_('Adresse du siège social'), blank=True, null=True)
    website = models.URLField(_('Site web'), blank=True, null=True)
    
    # Réseaux sociaux d'entreprise
    linkedin_company = models.URLField(_('LinkedIn Entreprise'), blank=True, null=True)
    twitter_company = models.URLField(_('Twitter Entreprise'), blank=True, null=True)
    facebook_company = models.URLField(_('Facebook Entreprise'), blank=True, null=True)
    
    # Informations financières (optionnelles)
    annual_revenue = models.DecimalField(
        _('Chiffre d\'affaires annuel'),
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('En euros')
    )
    funding_stage = models.CharField(
        _('Stade de financement'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Amorçage, Série A, B, C, etc.')
    )
    total_funding = models.DecimalField(
        _('Financement total levé'),
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('En euros')
    )
    
    # Statut de vérification
    is_verified = models.BooleanField(
        _('Entreprise vérifiée'),
        default=False,
        help_text=_('Indique si l\'entreprise a été vérifiée par l\'équipe VentureLink.')
    )
    verification_documents = models.FileField(
        _('Documents de vérification'),
        upload_to='company_verification/',
        blank=True,
        null=True,
        help_text=_('Kbis, statuts, etc.')
    )
    
    class Meta:
        verbose_name = _('profil d\'entreprise')
        verbose_name_plural = _('profils d\'entreprise')
        ordering = ['company_name']
    
    def __str__(self):
        return f"Profil entreprise - {self.company_name}"
    
    def get_display_name(self):
        """
        Retourne le nom d'affichage de l'entreprise.
        """
        return self.company_name or self.legal_name or "Entreprise sans nom"
    
    @property
    def is_startup(self):
        """
        Vérifie si l'entreprise est une startup.
        """
        return self.company_stage in ['IDEA', 'PROTOTYPE', 'MVP', 'EARLY_STAGE']
    
    @property
    def is_mature_company(self):
        """
        Vérifie si l'entreprise est mature.
        """
        return self.company_stage in ['GROWTH', 'MATURE']


class CompanyMember(TimeStampedModel, UUIDModel):
    """
    Modèle pour les membres/employés d'une entreprise.
    """
    ROLE_CHOICES = (
        ('CEO', _('PDG/CEO')),
        ('CTO', _('Directeur Technique')),
        ('CFO', _('Directeur Financier')),
        ('CMO', _('Directeur Marketing')),
        ('COO', _('Directeur des Opérations')),
        ('FOUNDER', _('Fondateur')),
        ('CO_FOUNDER', _('Co-fondateur')),
        ('DIRECTOR', _('Directeur')),
        ('MANAGER', _('Manager')),
        ('EMPLOYEE', _('Employé')),
        ('ADVISOR', _('Conseiller')),
        ('INVESTOR', _('Investisseur')),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('INACTIVE', _('Inactif')),
        ('PENDING', _('En attente')),
    )
    
    company_profile = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('Profil d\'entreprise')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_memberships',
        verbose_name=_('Utilisateur')
    )
    
    role = models.CharField(
        _('Rôle'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='EMPLOYEE'
    )
    title = models.CharField(_('Titre personnalisé'), max_length=100, blank=True, null=True)
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    start_date = models.DateField(_('Date de début'), blank=True, null=True)
    end_date = models.DateField(_('Date de fin'), blank=True, null=True)
    is_admin = models.BooleanField(
        _('Administrateur'),
        default=False,
        help_text=_('Peut gérer le profil de l\'entreprise')
    )
    
    class Meta:
        verbose_name = _('membre d\'entreprise')
        verbose_name_plural = _('membres d\'entreprise')
        unique_together = ('company_profile', 'user')
        ordering = ['-is_admin', 'role', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} chez {self.company_profile.company_name}"
    
    def get_display_title(self):
        """
        Retourne le titre d'affichage (personnalisé ou par défaut).
        """
        return self.title or self.get_role_display() 