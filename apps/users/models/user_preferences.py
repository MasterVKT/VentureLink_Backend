from django.db import models
from django.utils.translation import gettext_lazy as _
import json


class UserPreferences(models.Model):
    """
    Préférences utilisateur pour le matching IA.
    """
    RISK_LEVELS = [
        ('low', _('Faible')),
        ('medium', _('Moyen')),
        ('high', _('Élevé')),
    ]

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('Utilisateur')
    )

    # Préférences de catégories (stored as JSON for DB compatibility)
    _preferred_categories = models.TextField(
        _('Catégories préférées'),
        default='[]',
        blank=True,
        help_text=_("Liste des catégories préférées (ex: ['TECH', 'FINTECH'])")
    )

    # Préférences de budget
    min_investment_amount = models.DecimalField(
        _('Montant minimum d\'investissement'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Montant minimum d'investissement")
    )

    max_investment_amount = models.DecimalField(
        _('Montant maximum d\'investissement'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Montant maximum d'investissement")
    )

    # Préférences géographiques (stored as JSON for DB compatibility)
    _preferred_locations = models.TextField(
        _('Localisations préférées'),
        default='[]',
        blank=True,
        help_text=_("Localisations préférées")
    )

    # Tolérance au risque
    risk_tolerance = models.CharField(
        _('Tolérance au risque'),
        max_length=10,
        choices=RISK_LEVELS,
        default='medium'
    )

    # Historique d'interactions (stored as JSON for DB compatibility)
    _viewed_projects = models.TextField(
        _('Projets consultés'),
        default='[]',
        blank=True
    )

    favorited_projects_count = models.PositiveIntegerField(
        _('Nombre de projets en favoris'),
        default=0
    )
    
    invested_projects_count = models.PositiveIntegerField(
        _('Nombre de projets investis'),
        default=0
    )

    # Métadonnées
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('Préférences utilisateur')
        verbose_name_plural = _('Préférences utilisateur')
        ordering = ['-created_at']

    def __str__(self):
        return f"Preferences for {self.user.email}"

    # Property methods for ArrayField-like behavior
    @property
    def preferred_categories(self):
        try:
            return json.loads(self._preferred_categories) or []
        except (json.JSONDecodeError, TypeError):
            return []

    @preferred_categories.setter
    def preferred_categories(self, value):
        self._preferred_categories = json.dumps(value or [])

    @property
    def preferred_locations(self):
        try:
            return json.loads(self._preferred_locations) or []
        except (json.JSONDecodeError, TypeError):
            return []

    @preferred_locations.setter
    def preferred_locations(self, value):
        self._preferred_locations = json.dumps(value or [])

    @property
    def viewed_projects(self):
        try:
            return json.loads(self._viewed_projects) or []
        except (json.JSONDecodeError, TypeError):
            return []

    @viewed_projects.setter
    def viewed_projects(self, value):
        self._viewed_projects = json.dumps(value or [])
