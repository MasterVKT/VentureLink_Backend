from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, Profile, Subscription


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil lorsqu'un utilisateur est créé.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    """
    Crée automatiquement un abonnement gratuit lorsqu'un utilisateur est créé.
    """
    if created:
        Subscription.objects.create(
            user=instance,
            plan='FREE',
            status='ACTIVE',
            start_date=timezone.now(),
            auto_renew=False
        ) 