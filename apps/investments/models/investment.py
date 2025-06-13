"""
Models for investments management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.fields import MoneyField
from apps.users.models import User
from apps.projects.models.project import Project


class Investment(UUIDModel, TimeStampedModel):
    """
    Model representing an investment made by a user in a project.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_COMPLETED = 'COMPLETED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('En attente')),
        (STATUS_APPROVED, _('Approuvé')),
        (STATUS_REJECTED, _('Rejeté')),
        (STATUS_CANCELLED, _('Annulé')),
        (STATUS_COMPLETED, _('Complété')),
    ]
    
    TYPE_EQUITY = 'EQUITY'
    TYPE_LOAN = 'LOAN'
    TYPE_DONATION = 'DONATION'
    TYPE_CONVERTIBLE_NOTE = 'CONVERTIBLE_NOTE'
    
    TYPE_CHOICES = [
        (TYPE_EQUITY, _('Actions')),
        (TYPE_LOAN, _('Prêt')),
        (TYPE_DONATION, _('Don')),
        (TYPE_CONVERTIBLE_NOTE, _('Note convertible')),
    ]
    
    investor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='investments',
        verbose_name=_('Investisseur'),
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='investments',
        verbose_name=_('Projet'),
    )
    
    amount = MoneyField(
        _('Montant'),
        help_text=_('Montant de l\'investissement'),
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    
    investment_type = models.CharField(
        _('Type d\'investissement'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_EQUITY,
    )
    
    equity_percentage = models.DecimalField(
        _('Pourcentage d\'actions'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        help_text=_('Pourcentage d\'actions obtenues (si applicable)'),
    )
    
    interest_rate = models.DecimalField(
        _('Taux d\'intérêt'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Taux d\'intérêt annuel en pourcentage (si applicable)'),
    )
    
    term_months = models.PositiveIntegerField(
        _('Durée (mois)'),
        null=True,
        blank=True,
        help_text=_('Durée du prêt en mois (si applicable)'),
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    
    description = models.TextField(
        _('Description'),
        blank=True,
        null=True,
        help_text=_('Détails supplémentaires sur l\'investissement'),
    )
    
    contract_file = models.FileField(
        _('Contrat'),
        upload_to='investments/contracts/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('Document contractuel concernant l\'investissement'),
    )
    
    notes = models.TextField(
        _('Notes internes'),
        blank=True,
        null=True,
        help_text=_('Notes internes non visibles par les autres utilisateurs'),
    )
    
    approved_at = models.DateTimeField(
        _('Date d\'approbation'),
        null=True,
        blank=True,
    )
    
    completed_at = models.DateTimeField(
        _('Date de finalisation'),
        null=True,
        blank=True,
    )
    
    class Meta:
        verbose_name = _('Investissement')
        verbose_name_plural = _('Investissements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investor']),
            models.Index(fields=['project']),
            models.Index(fields=['status']),
            models.Index(fields=['investment_type']),
        ]
    
    def __str__(self):
        return f"{self.investor.email} - {self.project.title} - {self.amount} {self.currency}"


class InvestmentHistory(UUIDModel, TimeStampedModel):
    """
    Model representing the history of an investment status changes.
    """
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('Investissement'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='investment_history_changes',
        verbose_name=_('Utilisateur'),
        help_text=_('Utilisateur ayant effectué le changement'),
    )
    
    old_status = models.CharField(
        _('Ancien statut'),
        max_length=20,
        choices=Investment.STATUS_CHOICES,
        null=True,
        blank=True,
    )
    
    new_status = models.CharField(
        _('Nouveau statut'),
        max_length=20,
        choices=Investment.STATUS_CHOICES,
    )
    
    comment = models.TextField(
        _('Commentaire'),
        blank=True,
        null=True,
        help_text=_('Commentaire expliquant le changement'),
    )
    
    class Meta:
        verbose_name = _('Historique d\'investissement')
        verbose_name_plural = _('Historiques d\'investissements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investment']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.investment} - {self.old_status} → {self.new_status}"


class InvestmentPayment(UUIDModel, TimeStampedModel):
    """
    Model representing payment data for an investment.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_REFUNDED = 'REFUNDED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('En attente')),
        (STATUS_PROCESSING, _('En traitement')),
        (STATUS_COMPLETED, _('Complété')),
        (STATUS_FAILED, _('Échoué')),
        (STATUS_REFUNDED, _('Remboursé')),
    ]
    
    METHOD_BANK_TRANSFER = 'BANK_TRANSFER'
    METHOD_CREDIT_CARD = 'CREDIT_CARD'
    METHOD_PAYPAL = 'PAYPAL'
    METHOD_CRYPTO = 'CRYPTO'
    METHOD_OTHER = 'OTHER'
    
    METHOD_CHOICES = [
        (METHOD_BANK_TRANSFER, _('Virement bancaire')),
        (METHOD_CREDIT_CARD, _('Carte de crédit')),
        (METHOD_PAYPAL, _('PayPal')),
        (METHOD_CRYPTO, _('Cryptomonnaie')),
        (METHOD_OTHER, _('Autre')),
    ]
    
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Investissement'),
    )
    
    amount = MoneyField(
        _('Montant'),
        help_text=_('Montant du paiement'),
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    
    payment_method = models.CharField(
        _('Méthode de paiement'),
        max_length=20,
        choices=METHOD_CHOICES,
        default=METHOD_BANK_TRANSFER,
    )
    
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    
    transaction_id = models.CharField(
        _('ID de transaction'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Identifiant de la transaction (fourni par le processeur de paiement)'),
    )
    
    payment_details = models.JSONField(
        _('Détails du paiement'),
        blank=True,
        null=True,
        help_text=_('Données supplémentaires liées au paiement'),
    )
    
    receipt_file = models.FileField(
        _('Reçu'),
        upload_to='investments/receipts/%Y/%m/',
        null=True,
        blank=True,
        help_text=_('Reçu ou preuve de paiement'),
    )
    
    notes = models.TextField(
        _('Notes'),
        blank=True,
        null=True,
    )
    
    completed_at = models.DateTimeField(
        _('Date de complétion'),
        null=True,
        blank=True,
    )
    
    class Meta:
        verbose_name = _('Paiement d\'investissement')
        verbose_name_plural = _('Paiements d\'investissements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investment']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"{self.investment} - {self.amount} {self.currency} - {self.get_status_display()}" 