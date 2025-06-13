"""
Modèle de plan d'abonnement unifié pour VentureLink.
Ce modèle remplace la confusion entre PaymentPlan et Subscription.PLAN_CHOICES
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import TimeStampedModel


class SubscriptionPlan(TimeStampedModel):
    """
    Plans d'abonnement unifiés pour VentureLink.
    
    Ce modèle centralise tous les plans d'abonnement avec leurs prix
    dans toutes les devises supportées et leurs fonctionnalités.
    """
    
    # Utiliser string ID au lieu d'UUID pour une meilleure lisibilité
    id = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name=_('ID du plan'),
        help_text=_('Identifiant unique du plan (ex: basic_monthly, premium_yearly)')
    )
    
    # Informations de base
    name = models.CharField(_('Nom'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Prix multi-devises (OBLIGATOIRES pour tous les plans)
    price_eur = models.DecimalField(
        _('Prix en EUR'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_xaf = models.DecimalField(
        _('Prix en XAF'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_usd = models.DecimalField(
        _('Prix en USD'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Durée
    duration_days = models.PositiveIntegerField(
        _('Durée en jours'),
        help_text=_('Durée de validité de l\'abonnement en jours')
    )
    
    # Fonctionnalités (JSON structuré)
    features = models.JSONField(
        _('Fonctionnalités'),
        default=list,
        help_text=_('Liste des fonctionnalités incluses dans ce plan')
    )
    
    # Limites numériques (0 = illimité)
    max_projects = models.PositiveIntegerField(
        _('Nombre max de projets'), 
        default=0,
        help_text=_('Nombre maximum de projets (0 = illimité)')
    )
    max_investments = models.PositiveIntegerField(
        _('Nombre max d\'investissements'), 
        default=0,
        help_text=_('Nombre maximum d\'investissements (0 = illimité)')
    )
    max_messages = models.PositiveIntegerField(
        _('Nombre max de messages par mois'), 
        default=0,
        help_text=_('Nombre maximum de messages par mois (0 = illimité)')
    )
    
    # Fonctionnalités booléennes
    ai_matching = models.BooleanField(
        _('Matching IA'), 
        default=False,
        help_text=_('Accès au système de matching par intelligence artificielle')
    )
    priority_support = models.BooleanField(
        _('Support prioritaire'), 
        default=False,
        help_text=_('Support client prioritaire')
    )
    advanced_analytics = models.BooleanField(
        _('Analyses avancées'), 
        default=False,
        help_text=_('Accès aux analyses et statistiques avancées')
    )
    custom_branding = models.BooleanField(
        _('Personnalisation marque'), 
        default=False,
        help_text=_('Possibilité de personnaliser l\'interface')
    )
    
    # Configuration d'affichage
    is_active = models.BooleanField(_('Actif'), default=True)
    is_popular = models.BooleanField(
        _('Plan populaire'), 
        default=False,
        help_text=_('Marquer ce plan comme "plus populaire"')
    )
    is_free = models.BooleanField(
        _('Plan gratuit'), 
        default=False,
        help_text=_('Plan gratuit (tous les prix doivent être 0)')
    )
    sort_order = models.PositiveIntegerField(
        _('Ordre d\'affichage'), 
        default=0,
        help_text=_('Ordre d\'affichage dans la liste (plus petit = premier)')
    )
    
    # Essai gratuit
    trial_days = models.PositiveIntegerField(
        _('Jours d\'essai gratuit'), 
        default=0,
        help_text=_('Nombre de jours d\'essai gratuit (0 = pas d\'essai)')
    )
    
    # Identifiants externes pour My-CoolPay
    mycoolpay_plan_id = models.CharField(
        _('ID plan My-CoolPay'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Identifiant du plan dans My-CoolPay')
    )
    
    # Métadonnées supplémentaires
    metadata = models.JSONField(
        _('Métadonnées'), 
        default=dict, 
        blank=True,
        help_text=_('Données supplémentaires en format JSON')
    )
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('Plan d\'abonnement')
        verbose_name_plural = _('Plans d\'abonnement')
        ordering = ['sort_order', 'price_eur']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['is_popular']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.duration_days} jours)"
    
    def get_price_for_currency(self, currency_code):
        """
        Retourne le prix dans la devise demandée.
        
        Args:
            currency_code (str): Code de la devise ('EUR', 'XAF', 'USD')
            
        Returns:
            Decimal: Prix dans la devise demandée
        """
        price_map = {
            'EUR': self.price_eur,
            'XAF': self.price_xaf,
            'USD': self.price_usd,
        }
        return price_map.get(currency_code.upper(), self.price_eur)
    
    def get_currency_symbol(self, currency_code):
        """
        Retourne le symbole de la devise.
        
        Args:
            currency_code (str): Code de la devise
            
        Returns:
            str: Symbole de la devise
        """
        symbols = {
            'EUR': '€',
            'XAF': 'FCFA',
            'USD': '$',
        }
        return symbols.get(currency_code.upper(), '€')
    
    def format_price(self, currency_code):
        """
        Formate le prix avec le symbole de la devise.
        
        Args:
            currency_code (str): Code de la devise
            
        Returns:
            str: Prix formaté avec symbole
        """
        price = self.get_price_for_currency(currency_code)
        symbol = self.get_currency_symbol(currency_code)
        
        if currency_code.upper() == 'XAF':
            return f"{price:,.0f} {symbol}"
        else:
            return f"{price:,.2f} {symbol}"
    
    @property
    def duration_months(self):
        """
        Durée approximative en mois (pour compatibilité).
        
        Returns:
            int: Durée en mois (approximative)
        """
        return max(1, self.duration_days // 30)
    
    @property
    def is_unlimited_projects(self):
        """Vérifie si le plan permet un nombre illimité de projets."""
        return self.max_projects == 0
    
    @property
    def is_unlimited_investments(self):
        """Vérifie si le plan permet un nombre illimité d'investissements."""
        return self.max_investments == 0
    
    @property
    def is_unlimited_messages(self):
        """Vérifie si le plan permet un nombre illimité de messages."""
        return self.max_messages == 0
    
    def clean(self):
        """Validation des données du modèle."""
        from django.core.exceptions import ValidationError
        
        # Si c'est un plan gratuit, tous les prix doivent être 0
        if self.is_free:
            if any([self.price_eur > 0, self.price_xaf > 0, self.price_usd > 0]):
                raise ValidationError(
                    _('Un plan gratuit doit avoir tous ses prix à 0.')
                )
        
        # Vérifier que l'ID du plan suit la convention
        if self.id and not all(c.isalnum() or c == '_' for c in self.id):
            raise ValidationError(
                _('L\'ID du plan ne peut contenir que des lettres, chiffres et underscores.')
            )
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation."""
        self.clean()
        super().save(*args, **kwargs) 