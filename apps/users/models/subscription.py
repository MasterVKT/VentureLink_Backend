from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.core.models import TimeStampedModel, UUIDModel


class Subscription(TimeStampedModel, UUIDModel):
    """
    Modèle pour les abonnements premium des utilisateurs.
    """
    PLAN_CHOICES = (
        ('FREE', _('Gratuit')),
        ('PREMIUM_MONTHLY', _('Premium Mensuel')),
        ('PREMIUM_YEARLY', _('Premium Annuel')),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', _('Actif')),
        ('CANCELLED', _('Annulé')),
        ('EXPIRED', _('Expiré')),
        ('TRIAL', _('Période d\'essai')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_('Utilisateur')
    )
    plan = models.CharField(
        _('Plan'),
        max_length=20,
        choices=PLAN_CHOICES,
        default='FREE'
    )
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    auto_renew = models.BooleanField(_('Renouvellement automatique'), default=True)
    payment_provider = models.CharField(_('Fournisseur de paiement'), max_length=50, blank=True, null=True)
    payment_id = models.CharField(_('ID de paiement'), max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = _('abonnement')
        verbose_name_plural = _('abonnements')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_plan_display()} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """
        Vérifie si l'abonnement est actif.
        """
        return self.status == 'ACTIVE'
    
    @property
    def is_premium(self):
        """
        Vérifie si l'abonnement est premium.
        """
        return self.plan in ['PREMIUM_MONTHLY', 'PREMIUM_YEARLY'] and self.is_active
    
    def cancel(self):
        """
        Annule l'abonnement (désactive le renouvellement automatique).
        """
        self.auto_renew = False
        self.status = 'CANCELLED'
        self.save(update_fields=['auto_renew', 'status'])
    
    def expire(self):
        """
        Marque l'abonnement comme expiré.
        """
        self.status = 'EXPIRED'
        self.save(update_fields=['status'])
        
        # Mettre à jour le statut premium de l'utilisateur
        if self.user.is_premium:
            self.user.is_premium = False
            self.user.save(update_fields=['is_premium'])


class SubscriptionTransaction(TimeStampedModel, UUIDModel):
    """
    Modèle pour les transactions liées aux abonnements.
    """
    STATUS_CHOICES = (
        ('PENDING', _('En attente')),
        ('COMPLETED', _('Complétée')),
        ('FAILED', _('Échouée')),
        ('REFUNDED', _('Remboursée')),
    )
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Abonnement')
    )
    amount = models.DecimalField(_('Montant'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=3, default='EUR')
    transaction_id = models.CharField(_('ID de transaction'), max_length=255)
    payment_method = models.CharField(_('Méthode de paiement'), max_length=50)
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    error_message = models.TextField(_('Message d\'erreur'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('transaction d\'abonnement')
        verbose_name_plural = _('transactions d\'abonnement')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}" 