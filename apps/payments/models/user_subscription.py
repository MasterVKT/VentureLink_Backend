"""
Modèle d'abonnement utilisateur unifié pour VentureLink.
Ce modèle remplace la confusion entre Subscription dans users et PaymentSubscription dans payments.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from apps.core.models import TimeStampedModel
from .subscription_plan import SubscriptionPlan

User = get_user_model()


class UserSubscription(TimeStampedModel):
    """
    Abonnement utilisateur unifié.
    
    Ce modèle centralise tous les abonnements utilisateurs avec leur statut,
    leurs paiements et leur historique.
    """
    
    class SubscriptionStatus(models.TextChoices):
        """Statuts possibles d'un abonnement."""
        ACTIVE = 'ACTIVE', _('Actif')
        PENDING = 'PENDING', _('En attente')
        EXPIRED = 'EXPIRED', _('Expiré')
        CANCELLED = 'CANCELLED', _('Annulé')
        TRIAL = 'TRIAL', _('Période d\'essai')
        SUSPENDED = 'SUSPENDED', _('Suspendu')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Relations principales
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='payment_subscription',
        verbose_name=_('Utilisateur')
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Plan d\'abonnement')
    )
    
    # Statut et dates
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING
    )
    
    # Dates importantes
    started_at = models.DateTimeField(
        _('Commencé le'),
        help_text=_('Date de début de l\'abonnement')
    )
    expires_at = models.DateTimeField(
        _('Expire le'),
        help_text=_('Date d\'expiration de l\'abonnement')
    )
    trial_ends_at = models.DateTimeField(
        _('Fin de l\'essai'),
        null=True,
        blank=True,
        help_text=_('Date de fin de la période d\'essai gratuit')
    )
    cancelled_at = models.DateTimeField(
        _('Annulé le'),
        null=True,
        blank=True,
        help_text=_('Date d\'annulation par l\'utilisateur')
    )
    suspended_at = models.DateTimeField(
        _('Suspendu le'),
        null=True,
        blank=True,
        help_text=_('Date de suspension (non-paiement, etc.)')
    )
    
    # Configuration de renouvellement
    auto_renew = models.BooleanField(
        _('Renouvellement automatique'),
        default=True,
        help_text=_('L\'abonnement se renouvelle automatiquement')
    )
    next_billing_date = models.DateTimeField(
        _('Prochaine facturation'),
        null=True,
        blank=True,
        help_text=_('Date de la prochaine facturation automatique')
    )
    
    # Devise de facturation
    billing_currency = models.CharField(
        _('Devise de facturation'),
        max_length=3,
        choices=[
            ('EUR', 'Euro'),
            ('XAF', 'Franc CFA'),
            ('USD', 'Dollar US'),
        ],
        default='EUR',
        help_text=_('Devise utilisée pour les paiements de cet abonnement')
    )
    
    # Informations de paiement
    last_payment_date = models.DateTimeField(
        _('Dernier paiement'),
        null=True,
        blank=True,
        help_text=_('Date du dernier paiement réussi')
    )
    last_payment_amount = models.DecimalField(
        _('Montant dernier paiement'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Montant du dernier paiement réussi')
    )
    
    # Identifiants externes
    mycoolpay_subscription_id = models.CharField(
        _('ID abonnement My-CoolPay'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Identifiant de l\'abonnement dans My-CoolPay')
    )
    
    # Métadonnées
    metadata = models.JSONField(
        _('Métadonnées'),
        default=dict,
        blank=True,
        help_text=_('Données supplémentaires en format JSON')
    )
    
    # Notes administratives
    admin_notes = models.TextField(
        _('Notes administratives'),
        blank=True,
        help_text=_('Notes internes pour l\'équipe support')
    )
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('Abonnement utilisateur')
        verbose_name_plural = _('Abonnements utilisateurs')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['next_billing_date']),
            models.Index(fields=['auto_renew', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actuellement actif."""
        if self.status != self.SubscriptionStatus.ACTIVE:
            return False
        
        now = timezone.now()
        return self.expires_at > now
    
    @property
    def is_in_trial(self):
        """Vérifie si l'abonnement est en période d'essai."""
        if self.status != self.SubscriptionStatus.TRIAL:
            return False
        
        if not self.trial_ends_at:
            return False
        
        return timezone.now() < self.trial_ends_at
    
    @property
    def is_expired(self):
        """Vérifie si l'abonnement a expiré."""
        if self.status == self.SubscriptionStatus.EXPIRED:
            return True
        
        return timezone.now() > self.expires_at
    
    @property
    def days_remaining(self):
        """Nombre de jours restants avant expiration."""
        if self.is_expired:
            return 0
        
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)
    
    @property
    def trial_days_remaining(self):
        """Nombre de jours restants dans la période d'essai."""
        if not self.is_in_trial or not self.trial_ends_at:
            return 0
        
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)
    
    @property
    def current_period_price(self):
        """Prix de la période actuelle dans la devise de facturation."""
        return self.plan.get_price_for_currency(self.billing_currency)
    
    @property
    def formatted_current_price(self):
        """Prix de la période actuelle formaté avec devise."""
        return self.plan.format_price(self.billing_currency)
    
    def extend_subscription(self, days=None):
        """
        Prolonge l'abonnement.
        
        Args:
            days (int, optional): Nombre de jours à ajouter. 
                                 Si None, utilise la durée du plan.
        """
        if days is None:
            days = self.plan.duration_days
        
        self.expires_at += timedelta(days=days)
        
        # Si auto-renew activé, mettre à jour la prochaine facturation
        if self.auto_renew:
            self.next_billing_date = self.expires_at
        
        self.save(update_fields=['expires_at', 'next_billing_date'])
    
    def activate(self):
        """Active l'abonnement."""
        self.status = self.SubscriptionStatus.ACTIVE
        
        # Mettre à jour le statut premium de l'utilisateur
        if not self.user.is_premium:
            self.user.is_premium = True
            self.user.save(update_fields=['is_premium'])
        
        self.save(update_fields=['status'])
    
    def cancel(self, reason=None):
        """
        Annule l'abonnement.
        
        Args:
            reason (str, optional): Raison de l'annulation
        """
        self.status = self.SubscriptionStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        
        if reason:
            self.admin_notes += f"\nAnnulé le {timezone.now()}: {reason}"
        
        # Mettre à jour le statut premium de l'utilisateur
        if self.user.is_premium:
            self.user.is_premium = False
            self.user.save(update_fields=['is_premium'])
        
        self.save(update_fields=['status', 'cancelled_at', 'auto_renew', 'admin_notes'])
    
    def suspend(self, reason=None):
        """
        Suspend l'abonnement.
        
        Args:
            reason (str, optional): Raison de la suspension
        """
        self.status = self.SubscriptionStatus.SUSPENDED
        self.suspended_at = timezone.now()
        
        if reason:
            self.admin_notes += f"\nSuspendu le {timezone.now()}: {reason}"
        
        # Mettre à jour le statut premium de l'utilisateur
        if self.user.is_premium:
            self.user.is_premium = False
            self.user.save(update_fields=['is_premium'])
        
        self.save(update_fields=['status', 'suspended_at', 'admin_notes'])
    
    def expire(self):
        """Marque l'abonnement comme expiré."""
        self.status = self.SubscriptionStatus.EXPIRED
        
        # Mettre à jour le statut premium de l'utilisateur
        if self.user.is_premium:
            self.user.is_premium = False
            self.user.save(update_fields=['is_premium'])
        
        self.save(update_fields=['status'])
    
    def record_payment(self, amount, payment_date=None):
        """
        Enregistre un paiement réussi.
        
        Args:
            amount (Decimal): Montant du paiement
            payment_date (datetime, optional): Date du paiement
        """
        if payment_date is None:
            payment_date = timezone.now()
        
        self.last_payment_date = payment_date
        self.last_payment_amount = amount
        
        # Si c'était en attente, activer
        if self.status == self.SubscriptionStatus.PENDING:
            self.activate()
        
        # Prolonger l'abonnement
        self.extend_subscription()
        
        self.save(update_fields=['last_payment_date', 'last_payment_amount'])
    
    def start_trial(self):
        """Démarre une période d'essai gratuit."""
        if self.plan.trial_days > 0:
            self.status = self.SubscriptionStatus.TRIAL
            self.trial_ends_at = timezone.now() + timedelta(days=self.plan.trial_days)
            self.expires_at = self.trial_ends_at
            
            self.save(update_fields=['status', 'trial_ends_at', 'expires_at'])
            return True
        return False
    
    @classmethod
    def create_subscription(cls, user, plan, billing_currency='EUR', start_trial=True):
        """
        Crée un nouvel abonnement pour un utilisateur.
        
        Args:
            user: Utilisateur
            plan: Plan d'abonnement
            billing_currency: Devise de facturation
            start_trial: Démarrer avec un essai gratuit si disponible
            
        Returns:
            UserSubscription: Nouvel abonnement créé
        """
        now = timezone.now()
        
        # Calculer les dates
        if start_trial and plan.trial_days > 0:
            # Période d'essai
            expires_at = now + timedelta(days=plan.trial_days)
            status = cls.SubscriptionStatus.TRIAL
            trial_ends_at = expires_at
        else:
            # Abonnement normal
            expires_at = now + timedelta(days=plan.duration_days)
            status = cls.SubscriptionStatus.PENDING
            trial_ends_at = None
        
        subscription = cls.objects.create(
            user=user,
            plan=plan,
            status=status,
            started_at=now,
            expires_at=expires_at,
            trial_ends_at=trial_ends_at,
            billing_currency=billing_currency,
            next_billing_date=expires_at if status != cls.SubscriptionStatus.TRIAL else None
        )
        
        return subscription 