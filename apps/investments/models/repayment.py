"""
Models for investment repayments management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel
from apps.core.fields import MoneyField
from apps.users.models import User
from apps.investments.models.investment import Investment, InvestmentPayment


class Repayment(UUIDModel, TimeStampedModel):
    """
    Model representing a repayment from a project to an investor.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('En attente')),
        (STATUS_PROCESSING, _('En traitement')),
        (STATUS_COMPLETED, _('Complété')),
        (STATUS_FAILED, _('Échoué')),
    ]
    
    TYPE_PRINCIPAL = 'PRINCIPAL'
    TYPE_INTEREST = 'INTEREST'
    TYPE_DIVIDEND = 'DIVIDEND'
    TYPE_MIXED = 'MIXED'
    
    TYPE_CHOICES = [
        (TYPE_PRINCIPAL, _('Principal')),
        (TYPE_INTEREST, _('Intérêts')),
        (TYPE_DIVIDEND, _('Dividende')),
        (TYPE_MIXED, _('Mixte')),
    ]
    
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='repayments',
        verbose_name=_('Investissement'),
    )
    
    paid_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='repayments_sent',
        verbose_name=_('Payé par'),
        help_text=_('Utilisateur ayant effectué le paiement (généralement le créateur du projet)'),
    )
    
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='repayments_received',
        verbose_name=_('Reçu par'),
        help_text=_('Utilisateur ayant reçu le paiement (généralement l\'investisseur)'),
    )
    
    amount = MoneyField(
        _('Montant'),
        help_text=_('Montant du remboursement'),
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    
    repayment_type = models.CharField(
        _('Type de remboursement'),
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_PRINCIPAL,
    )
    
    principal_amount = MoneyField(
        _('Montant principal'),
        null=True,
        blank=True,
        help_text=_('Partie du montant correspondant au principal'),
    )
    
    interest_amount = MoneyField(
        _('Montant des intérêts'),
        null=True,
        blank=True,
        help_text=_('Partie du montant correspondant aux intérêts'),
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
    
    payment_method = models.CharField(
        _('Méthode de paiement'),
        max_length=20,
        choices=InvestmentPayment.METHOD_CHOICES,
        default=InvestmentPayment.METHOD_BANK_TRANSFER,
    )
    
    payment_details = models.JSONField(
        _('Détails du paiement'),
        blank=True,
        null=True,
        help_text=_('Données supplémentaires liées au paiement'),
    )
    
    receipt_file = models.FileField(
        _('Reçu'),
        upload_to='investments/repayments/%Y/%m/',
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
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['investment']),
            models.Index(fields=['status']),
            models.Index(fields=['repayment_type']),
        ]
    
    def __str__(self):
        return f"{self.investment} - {self.get_repayment_type_display()} - {self.amount} {self.currency}"


class RepaymentSchedule(UUIDModel, TimeStampedModel):
    """
    Model representing a scheduled repayment for a loan investment.
    """
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='repayment_schedule',
        verbose_name=_('Investissement'),
    )
    
    due_date = models.DateField(
        _('Date d\'échéance'),
        help_text=_('Date prévue pour le remboursement'),
    )
    
    amount = MoneyField(
        _('Montant total'),
        help_text=_('Montant total du remboursement prévu'),
    )
    
    principal_amount = MoneyField(
        _('Montant principal'),
        help_text=_('Partie du montant correspondant au principal'),
    )
    
    interest_amount = MoneyField(
        _('Montant des intérêts'),
        help_text=_('Partie du montant correspondant aux intérêts'),
    )
    
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR',
        help_text=_('Code ISO de la devise (EUR, USD, etc.)'),
    )
    
    is_paid = models.BooleanField(
        _('Payé'),
        default=False,
        help_text=_('Indique si ce paiement programmé a été effectué'),
    )
    
    repayment = models.OneToOneField(
        Repayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_item',
        verbose_name=_('Remboursement'),
        help_text=_('Remboursement associé à cette échéance'),
    )
    
    notes = models.TextField(
        _('Notes'),
        blank=True,
        null=True,
    )
    
    class Meta:
        verbose_name = _('Échéance de remboursement')
        verbose_name_plural = _('Échéances de remboursement')
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['investment']),
            models.Index(fields=['due_date']),
            models.Index(fields=['is_paid']),
        ]
    
    def __str__(self):
        return f"{self.investment} - {self.due_date} - {self.amount} {self.currency}" 