"""
Modèle de paiement pour l'intégration avec My-CoolPay.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.core.models import TimeStampedModel

User = get_user_model()


class Payment(TimeStampedModel):
    """
    Modèle pour stocker les informations de paiement.
    
    Ce modèle enregistre les détails des paiements effectués via My-CoolPay
    et conserve un lien avec l'objet qui a été payé (projet, abonnement, etc.)
    via une relation générique.
    """
    
    class PaymentStatus(models.TextChoices):
        """Statuts possibles d'un paiement."""
        PENDING = 'PENDING', _('En attente')
        PROCESSING = 'PROCESSING', _('En cours de traitement')
        COMPLETED = 'COMPLETED', _('Complété')
        FAILED = 'FAILED', _('Échoué')
        REFUNDED = 'REFUNDED', _('Remboursé')
        PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED', _('Partiellement remboursé')
        CANCELLED = 'CANCELLED', _('Annulé')
    
    class PaymentType(models.TextChoices):
        """Types de paiement possibles."""
        SUBSCRIPTION = 'SUBSCRIPTION', _('Abonnement')
        INVESTMENT = 'INVESTMENT', _('Investissement')
        TIP = 'TIP', _('Pourboire')
        SERVICE_FEE = 'SERVICE_FEE', _('Frais de service')
        OTHER = 'OTHER', _('Autre')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Utilisateur qui effectue le paiement
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name=_('Utilisateur')
    )
    
    # Relation générique vers l'objet concerné par le paiement
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Type de contenu')
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('ID de l\'objet')
    )
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Détails du paiement
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    currency = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name=_('Devise')
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_('Statut')
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.OTHER,
        verbose_name=_('Type de paiement')
    )
    
    # Identifiants externes pour My-CoolPay
    external_payment_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('ID de paiement externe')
    )
    external_checkout_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('URL de paiement externe')
    )
    
    # Métadonnées et description
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Métadonnées')
    )
    
    # Dates importantes
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )
    
    # Indicateurs
    is_test = models.BooleanField(
        default=False,
        verbose_name=_('Paiement de test')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        app_label = 'payments'
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='payments_status_idx'),
            models.Index(fields=['user'], name='payments_user_idx'),
            models.Index(fields=['payment_type'], name='payments_type_idx'),
            models.Index(fields=['external_payment_id'], name='payments_ext_id_idx'),
        ]
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"Paiement de {self.amount} {self.currency} - {self.get_status_display()}"
    
    @property
    def is_completed(self):
        """Indique si le paiement est complété."""
        return self.status == self.PaymentStatus.COMPLETED
    
    @property
    def is_refunded(self):
        """Indique si le paiement a été remboursé."""
        return self.status in [
            self.PaymentStatus.REFUNDED, 
            self.PaymentStatus.PARTIALLY_REFUNDED
        ]
    
    @property
    def can_be_refunded(self):
        """Indique si le paiement peut être remboursé."""
        return self.status == self.PaymentStatus.COMPLETED


class Refund(TimeStampedModel):
    """
    Modèle pour stocker les informations de remboursement.
    
    Ce modèle enregistre les détails des remboursements effectués
    via My-CoolPay.
    """
    
    class RefundStatus(models.TextChoices):
        """Statuts possibles d'un remboursement."""
        PENDING = 'PENDING', _('En attente')
        PROCESSING = 'PROCESSING', _('En cours de traitement')
        COMPLETED = 'COMPLETED', _('Complété')
        FAILED = 'FAILED', _('Échoué')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Lien vers le paiement remboursé
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_('Paiement')
    )
    
    # Détails du remboursement
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_('Montant')
    )
    currency = models.CharField(
        max_length=3,
        verbose_name=_('Devise')
    )
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        verbose_name=_('Statut')
    )
    
    # Identifiants externes
    external_refund_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('ID de remboursement externe')
    )
    
    # Raison et notes
    reason = models.TextField(
        blank=True,
        verbose_name=_('Raison')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    # Dates importantes
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Complété le')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        app_label = 'payments'
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='refunds_status_idx'),
            models.Index(fields=['payment'], name='refunds_payment_idx'),
            models.Index(fields=['external_refund_id'], name='refunds_ext_id_idx'),
        ]
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"Remboursement de {self.amount} {self.currency} - {self.get_status_display()}"
    
    @property
    def is_completed(self):
        """Indique si le remboursement est complété."""
        return self.status == self.RefundStatus.COMPLETED


class Currency(models.TextChoices):
    """
    Devises supportées par l'application.
    """
    XAF = 'XAF', _('Franc CFA')
    EUR = 'EUR', _('Euro')
    USD = 'USD', _('Dollar US')


class PaymentMethod(TimeStampedModel):
    """
    Méthodes de paiement disponibles via My-CoolPay.
    """
    METHOD_TYPES = (
        ('MOBILE_MONEY', _('Mobile Money')),
        ('BANK_CARD', _('Carte Bancaire')),
        ('BANK_TRANSFER', _('Virement Bancaire')),
        ('CASH', _('Espèces')),
    )
    
    MOBILE_OPERATORS = (
        ('ORANGE', _('Orange Money')),
        ('MTN', _('MTN Mobile Money')),
        ('MOOV', _('Moov Money')),
        ('EXPRESSU', _('Express Union')),
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    name = models.CharField(_('Nom'), max_length=100)
    type = models.CharField(_('Type'), max_length=20, choices=METHOD_TYPES)
    operator = models.CharField(_('Opérateur'), max_length=20, choices=MOBILE_OPERATORS, blank=True, null=True)
    is_active = models.BooleanField(_('Actif'), default=True)
    supported_currencies = models.JSONField(_('Devises supportées'), default=list)
    fee_percentage = models.DecimalField(_('Pourcentage de frais'), max_digits=5, decimal_places=2, default=0)
    fee_fixed = models.DecimalField(_('Frais fixes'), max_digits=10, decimal_places=2, default=0)
    min_amount = models.DecimalField(_('Montant minimum'), max_digits=15, decimal_places=2, default=0)
    max_amount = models.DecimalField(_('Montant maximum'), max_digits=15, decimal_places=2, default=999999999)
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('méthode de paiement')
        verbose_name_plural = _('méthodes de paiement')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def calculate_fees(self, amount):
        """
        Calcule les frais pour un montant donné.
        """
        percentage_fee = amount * (self.fee_percentage / 100)
        total_fees = percentage_fee + self.fee_fixed
        return total_fees
    
    def is_amount_valid(self, amount):
        """
        Vérifie si le montant est dans les limites autorisées.
        """
        return self.min_amount <= amount <= self.max_amount


class PaymentPlan(TimeStampedModel):
    """
    Plans d'abonnement disponibles.
    """
    BILLING_CYCLES = (
        ('MONTHLY', _('Mensuel')),
        ('YEARLY', _('Annuel')),
        ('WEEKLY', _('Hebdomadaire')),
        ('DAILY', _('Quotidien')),
    )
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Prix dans différentes devises
    price_xaf = models.DecimalField(_('Prix en XAF'), max_digits=10, decimal_places=2, default=0)
    price_eur = models.DecimalField(_('Prix en EUR'), max_digits=10, decimal_places=2, default=0)
    price_usd = models.DecimalField(_('Prix en USD'), max_digits=10, decimal_places=2, default=0)
    
    billing_cycle = models.CharField(_('Cycle de facturation'), max_length=20, choices=BILLING_CYCLES)
    trial_days = models.PositiveIntegerField(_('Jours d\'essai'), default=0)
    
    # Champs de compatibilité
    price = models.DecimalField(_('Prix par défaut'), max_digits=10, decimal_places=2, default=0, help_text=_('Prix par défaut en XAF'))
    currency = models.CharField(_('Devise par défaut'), max_length=3, default='XAF', help_text=_('Devise par défaut'))
    duration_months = models.PositiveIntegerField(_('Durée en mois'), default=1, help_text=_('Durée de l\'abonnement en mois'))
    
    # Fonctionnalités
    features = models.JSONField(_('Fonctionnalités'), default=list)
    max_projects = models.PositiveIntegerField(_('Nombre max de projets'), default=0)  # 0 = illimité
    max_investments = models.PositiveIntegerField(_('Nombre max d\'investissements'), default=0)  # 0 = illimité
    priority_support = models.BooleanField(_('Support prioritaire'), default=False)
    advanced_analytics = models.BooleanField(_('Analyses avancées'), default=False)
    
    # Configuration
    is_active = models.BooleanField(_('Actif'), default=True)
    is_popular = models.BooleanField(_('Populaire'), default=False)
    sort_order = models.PositiveIntegerField(_('Ordre d\'affichage'), default=0)
    
    # Identifiants externes
    external_plan_id = models.CharField(_('ID plan externe'), max_length=255, blank=True, null=True)
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('plan de paiement')
        verbose_name_plural = _('plans de paiement')
        ordering = ['sort_order', 'price_xaf']
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_cycle_display()}"
    
    def get_price_in_currency(self, currency):
        """
        Retourne le prix dans la devise demandée.
        """
        price_map = {
            Currency.XAF: self.price_xaf,
            Currency.EUR: self.price_eur,
            Currency.USD: self.price_usd,
        }
        return price_map.get(currency, self.price_xaf)
    
    @property
    def display_price(self):
        """
        Prix d'affichage par défaut en XAF.
        """
        return f"{self.price_xaf} XAF"


class PaymentSubscription(TimeStampedModel):
    """
    Abonnements actifs des utilisateurs pour les paiements.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_subscriptions',
        verbose_name=_('Utilisateur')
    )
    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.PROTECT,
        related_name='payment_subscriptions',
        verbose_name=_('Plan')
    )
    
    # Statut et dates
    status = models.CharField(_('Statut'), max_length=30, choices=Payment.PaymentStatus.choices, default=Payment.PaymentStatus.PENDING)
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    next_billing_date = models.DateTimeField(_('Prochaine facturation'), blank=True, null=True)
    
    # Configuration
    auto_renew = models.BooleanField(_('Renouvellement automatique'), default=True)
    currency = models.CharField(_('Devise de facturation'), max_length=3, choices=Currency.choices, default=Currency.XAF)
    is_active = models.BooleanField(_('Actif'), default=False, help_text=_('Indique si l\'abonnement est actuellement actif'))
    
    # Paiement
    last_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_renewals',
        verbose_name=_('Dernier paiement')
    )
    
    # Identifiants externes
    external_subscription_id = models.CharField(_('ID abonnement externe'), max_length=255, blank=True, null=True)
    
    # Métadonnées
    metadata = models.JSONField(_('Métadonnées'), default=dict, blank=True)
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('abonnement de paiement')
        verbose_name_plural = _('abonnements de paiement')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['next_billing_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """
        Vérifie si l'abonnement est actif.
        """
        return self.status == Payment.PaymentStatus.COMPLETED
    
    @property
    def days_remaining(self):
        """
        Nombre de jours restants avant la fin de l'abonnement.
        """
        if not self.end_date:
            return None
        
        from django.utils import timezone
        delta = self.end_date - timezone.now()
        return max(0, delta.days) 