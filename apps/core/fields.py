"""
Custom field types for the application.
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class MoneyField(models.DecimalField):
    """
    A custom field for monetary values with support for currency.
    """
    
    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs.setdefault('max_digits', 14)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('validators', [MinValueValidator(Decimal('0'))])
        super().__init__(verbose_name, name, **kwargs)
        
    def formfield(self, **kwargs):
        defaults = {'min_value': Decimal('0')}
        defaults.update(kwargs)
        return super().formfield(**defaults) 