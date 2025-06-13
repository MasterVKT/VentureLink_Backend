from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator

from apps.core.utils import get_currency_choices


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés.
        """
        if not email:
            raise ValueError(_('L\'email est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec l'email et le mot de passe donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé qui utilise l'email comme identifiant unique
    au lieu d'un nom d'utilisateur.
    """
    USER_TYPE_CHOICES = (
        ('INVESTOR', _('Investisseur')),
        ('PROJECT_OWNER', _('Porteur de projet')),
        ('BOTH', _('Les deux')),
        ('ADMIN', _('Administrateur')),
    )
    
    LANGUAGE_CHOICES = (
        ('fr', _('Français')),
        ('en', _('Anglais')),
    )
    
    # Validateur pour les numéros de téléphone
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'. 9 à 15 chiffres autorisés.")
    )
    
    # Champs de base
    email = models.EmailField(_('Adresse email'), unique=True)
    first_name = models.CharField(_('Prénom'), max_length=150, blank=True)
    last_name = models.CharField(_('Nom'), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _('Staff'),
        default=False,
        help_text=_('Indique si l\'utilisateur peut se connecter au site d\'administration.'),
    )
    is_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_(
            'Indique si l\'utilisateur doit être considéré comme actif. '
            'Décochez ceci plutôt que de supprimer des comptes.'
        ),
    )
    date_joined = models.DateTimeField(_('Date d\'inscription'), default=timezone.now)
    
    # Champs spécifiques à VentureLink
    user_type = models.CharField(
        _('Type d\'utilisateur'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='BOTH',
    )
    phone_number = models.CharField(
        _('Numéro de téléphone'),
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True
    )
    location = models.CharField(_('Localisation'), max_length=255, blank=True, null=True)
    language = models.CharField(
        _('Langue'),
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='fr',
    )
    is_verified = models.BooleanField(
        _('Vérifié'),
        default=False,
        help_text=_('Indique si l\'utilisateur a vérifié son identité.'),
    )
    is_premium = models.BooleanField(
        _('Premium'),
        default=False,
        help_text=_('Indique si l\'utilisateur a un abonnement premium actif.'),
    )
    fcm_token = models.CharField(
        _('Token FCM'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Token Firebase Cloud Messaging pour les notifications push.'),
    )
    preferred_currency = models.CharField(
        _('Devise préférée'),
        max_length=3,
        choices=get_currency_choices(),
        default='EUR',
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['email']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Retourne le prénom et le nom avec un espace au milieu.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """
        Retourne le prénom de l'utilisateur.
        """
        return self.first_name
    
    @property
    def is_investor(self):
        """
        Vérifie si l'utilisateur est un investisseur.
        """
        return self.user_type in ['INVESTOR', 'BOTH']
    
    @property
    def is_project_owner(self):
        """
        Vérifie si l'utilisateur est un porteur de projet.
        """
        return self.user_type in ['PROJECT_OWNER', 'BOTH'] 