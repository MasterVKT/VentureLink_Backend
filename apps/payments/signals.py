"""
Signaux pour l'application payments.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

# Les modèles seront importés une fois qu'ils auront été créés
# from apps.payments.models import Payment 