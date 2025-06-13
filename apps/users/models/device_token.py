"""
Modèle pour gérer les tokens des appareils des utilisateurs.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.core.models import TimeStampedModel, UUIDModel


class DeviceToken(TimeStampedModel, UUIDModel):
    """
    Modèle pour stocker les tokens FCM des appareils des utilisateurs.
    """
    PLATFORM_CHOICES = (
        ('android', _('Android')),
        ('ios', _('iOS')),
        ('web', _('Web')),
        ('desktop', _('Desktop')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name=_('Utilisateur')
    )
    
    token = models.CharField(
        _('Token FCM'),
        max_length=255,
        unique=True,
        help_text=_('Token Firebase Cloud Messaging pour l\'appareil')
    )
    
    platform = models.CharField(
        _('Plateforme'),
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='android',
        help_text=_('Plateforme de l\'appareil')
    )
    
    device_id = models.CharField(
        _('ID de l\'appareil'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Identifiant unique de l\'appareil')
    )
    
    device_name = models.CharField(
        _('Nom de l\'appareil'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Nom de l\'appareil (ex: iPhone de Jean)')
    )
    
    app_version = models.CharField(
        _('Version de l\'application'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Version de l\'application installée')
    )
    
    is_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Indique si le token est actif et peut recevoir des notifications')
    )
    
    last_used_at = models.DateTimeField(
        _('Dernière utilisation'),
        auto_now=True,
        help_text=_('Date de dernière utilisation du token')
    )
    
    class Meta:
        verbose_name = _('token d\'appareil')
        verbose_name_plural = _('tokens d\'appareils')
        ordering = ['-created_at']
        unique_together = ['user', 'device_id']  # Un utilisateur ne peut avoir qu'un token par appareil
    
    def __str__(self):
        return f"{self.user.email} - {self.platform} - {self.device_name or 'Appareil inconnu'}"
    
    def update_token(self, new_token):
        """
        Met à jour le token de l'appareil.
        
        Args:
            new_token (str): Le nouveau token FCM
        """
        self.token = new_token
        self.is_active = True
        self.save(update_fields=['token', 'is_active', 'updated_at'])
    
    def deactivate(self):
        """
        Désactive le token.
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at']) 