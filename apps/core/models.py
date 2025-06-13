import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Un modèle abstrait qui fournit des champs de suivi de création et de modification automatiques.
    """
    created_at = models.DateTimeField(_('Date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date de modification'), auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Un modèle abstrait qui utilise UUID comme clé primaire.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Identifiant')
    )

    class Meta:
        abstract = True


class CurrencyField(models.DecimalField):
    """
    Champ personnalisé pour les valeurs monétaires.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', 14)
        kwargs.setdefault('decimal_places', 2)
        super().__init__(*args, **kwargs) 