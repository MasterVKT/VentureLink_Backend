"""
Modèles pour les analytics et les métriques.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from apps.core.models import TimeStampedModel

User = get_user_model()


class UserMetrics(TimeStampedModel):
    """
    Métriques associées à un utilisateur.
    
    Ce modèle stocke les métriques cumulatives pour chaque utilisateur,
    comme le nombre de projets créés, le nombre de vues sur ses projets, etc.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name=_('Utilisateur')
    )
    
    # Métriques générales
    projects_created_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de projets créés')
    )
    projects_published_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de projets publiés')
    )
    
    # Métriques d'engagement
    total_project_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total de vues sur les projets')
    )
    total_project_interests = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total d\'intérêts exprimés pour les projets')
    )
    total_comments_received = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total de commentaires reçus')
    )
    
    # Métriques d'investissement
    investments_made_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'investissements réalisés')
    )
    total_investment_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_('Montant total investi')
    )
    
    # Métriques de messagerie
    messages_sent_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de messages envoyés')
    )
    messages_received_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de messages reçus')
    )
    
    # Métriques de connexion
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Dernière connexion')
    )
    login_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de connexions')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        verbose_name = _('Métriques utilisateur')
        verbose_name_plural = _('Métriques utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"Métriques de {self.user.email}"


class ProjectMetrics(TimeStampedModel):
    """
    Métriques associées à un projet.
    
    Ce modèle stocke les métriques cumulatives pour chaque projet,
    comme le nombre de vues, le nombre d'intérêts exprimés, etc.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Relation générique vers le projet
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Type de contenu')
    )
    object_id = models.UUIDField(verbose_name=_('ID de l\'objet'))
    project = GenericForeignKey('content_type', 'object_id')
    
    # Métriques de base
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de vues')
    )
    interest_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'intérêts exprimés')
    )
    favorite_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de favoris')
    )
    
    # Métriques d'interaction
    comment_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de commentaires')
    )
    share_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de partages')
    )
    
    # Métriques d'investissement
    investment_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'investissements')
    )
    total_investment_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_('Montant total investi')
    )
    
    # Métriques de conversion
    view_to_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Taux de conversion vues/intérêts (%)')
    )
    interest_to_investment_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Taux de conversion intérêts/investissements (%)')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        verbose_name = _('Métriques projet')
        verbose_name_plural = _('Métriques projets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"Métriques du projet {self.object_id}"
    
    def update_conversion_rates(self):
        """Mettre à jour les taux de conversion."""
        # Calculer le taux de conversion vues -> intérêts
        if self.view_count > 0:
            self.view_to_interest_rate = (self.interest_count / self.view_count) * 100
        
        # Calculer le taux de conversion intérêts -> investissements
        if self.interest_count > 0:
            self.interest_to_investment_rate = (self.investment_count / self.interest_count) * 100
        
        self.save(update_fields=['view_to_interest_rate', 'interest_to_investment_rate'])


class DailyMetrics(TimeStampedModel):
    """
    Métriques quotidiennes de la plateforme.
    
    Ce modèle stocke les métriques agrégées pour chaque jour,
    comme le nombre de nouveaux utilisateurs, le nombre de projets créés, etc.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    date = models.DateField(
        unique=True,
        verbose_name=_('Date')
    )
    
    # Métriques utilisateurs
    new_users_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de nouveaux utilisateurs')
    )
    active_users_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'utilisateurs actifs')
    )
    
    # Métriques projets
    new_projects_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de nouveaux projets')
    )
    published_projects_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de projets publiés')
    )
    
    # Métriques d'engagement
    total_views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total de vues')
    )
    total_interests_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total d\'intérêts exprimés')
    )
    
    # Métriques financières
    total_investment_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_('Montant total investi')
    )
    new_subscriptions_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre de nouveaux abonnements')
    )
    subscription_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name=_('Revenus des abonnements')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        verbose_name = _('Métriques quotidiennes')
        verbose_name_plural = _('Métriques quotidiennes')
        ordering = ['-date']
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"Métriques du {self.date}"


class EventLog(TimeStampedModel):
    """
    Journal des événements pour l'analytique.
    
    Ce modèle enregistre les événements individuels qui se produisent sur la plateforme,
    comme les vues de projets, les intérêts exprimés, etc.
    """
    class EventType(models.TextChoices):
        """Types d'événements possibles."""
        PROJECT_VIEW = 'PROJECT_VIEW', _('Vue de projet')
        PROJECT_INTEREST = 'PROJECT_INTEREST', _('Intérêt pour un projet')
        PROJECT_FAVORITE = 'PROJECT_FAVORITE', _('Ajout aux favoris')
        PROJECT_COMMENT = 'PROJECT_COMMENT', _('Commentaire sur un projet')
        PROJECT_SHARE = 'PROJECT_SHARE', _('Partage de projet')
        USER_LOGIN = 'USER_LOGIN', _('Connexion utilisateur')
        USER_REGISTRATION = 'USER_REGISTRATION', _('Inscription utilisateur')
        INVESTMENT_MADE = 'INVESTMENT_MADE', _('Investissement réalisé')
        MESSAGE_SENT = 'MESSAGE_SENT', _('Message envoyé')
        SUBSCRIPTION_STARTED = 'SUBSCRIPTION_STARTED', _('Abonnement démarré')
        SUBSCRIPTION_RENEWED = 'SUBSCRIPTION_RENEWED', _('Abonnement renouvelé')
        SUBSCRIPTION_CANCELED = 'SUBSCRIPTION_CANCELED', _('Abonnement annulé')
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Type d'événement
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        verbose_name=_('Type d\'événement')
    )
    
    # Utilisateur concerné (optionnel)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_('Utilisateur')
    )
    
    # Objet concerné (relation générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
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
    
    # Données supplémentaires
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Métadonnées')
    )
    
    # Adresse IP et user agent
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        verbose_name = _('Journal d\'événement')
        verbose_name_plural = _('Journal d\'événements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['user']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        return f"{self.get_event_type_display()} - {self.created_at}"


class ReferralTracker(TimeStampedModel):
    """
    Suivi des sources de trafic et des référencements.
    
    Ce modèle enregistre les informations sur les sources de trafic
    et les campagnes marketing.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    
    # Source et référent
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Source')
    )
    referrer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_('Site référent')
    )
    
    # Paramètres de campagne
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UTM Source')
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UTM Medium')
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UTM Campaign')
    )
    utm_term = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UTM Term')
    )
    utm_content = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UTM Content')
    )
    
    # Utilisateur concerné (si connecté)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name=_('Utilisateur')
    )
    
    # Action réalisée
    action = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Action réalisée')
    )
    
    # Adresse IP et user agent
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    
    class Meta:
        """Métadonnées du modèle."""
        verbose_name = _('Suivi de référencement')
        verbose_name_plural = _('Suivi de référencement')
        ordering = ['-created_at']
    
    def __str__(self):
        """Représentation textuelle de l'objet."""
        if self.utm_campaign:
            return f"Campagne: {self.utm_campaign} ({self.created_at})"
        elif self.source:
            return f"Source: {self.source} ({self.created_at})"
        else:
            return f"Référencement du {self.created_at}"
