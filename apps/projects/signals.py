"""
Signal receivers for the projects app.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.projects.models.project_interaction import ProjectInterest, ProjectFavorite
from apps.projects.models.project_media import ProjectMedia


@receiver(post_delete, sender=ProjectInterest)
def update_project_interest_count_on_delete(sender, instance, **kwargs):
    """
    Update project interest count when interest is deleted.
    """
    if instance.project.interests_count > 0:
        instance.project.interests_count -= 1
        instance.project.save(update_fields=['interests_count'])


@receiver(post_delete, sender=ProjectFavorite)
def update_project_favorite_count_on_delete(sender, instance, **kwargs):
    """
    Update project favorite count when favorite is deleted.
    """
    if instance.project.favorites_count > 0:
        instance.project.favorites_count -= 1
        instance.project.save(update_fields=['favorites_count'])


@receiver(post_delete, sender=ProjectMedia)
def cleanup_project_media_on_delete(sender, instance, **kwargs):
    """
    Clean up media file when ProjectMedia instance is deleted.
    """
    # Delete file from storage if it exists
    if instance.file:
        storage, path = instance.file.storage, instance.file.path
        try:
            storage.delete(path)
        except Exception:
            pass  # Ignorer les erreurs de suppression de fichier 