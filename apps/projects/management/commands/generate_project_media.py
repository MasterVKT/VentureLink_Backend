"""
Commande Django pour générer et associer des médias aux projets existants.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.projects.models import Project
from apps.projects.services.project_media_service import ProjectMediaService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande pour générer des images de placeholder pour les projets existants.
    
    Usage:
        python manage.py generate_project_media
        python manage.py generate_project_media --project-id UUID
        python manage.py generate_project_media --source unsplash
    """
    
    help = 'Génère et associe des médias aux projets existants'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=str,
            help='ID du projet spécifique à traiter',
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['placeholder', 'unsplash', 'generated'],
            default='generated',
            help='Source des images à utiliser',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Remplacer les médias existants',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Nombre d\'images par projet',
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal de la commande"""
        self.stdout.write(
            self.style.SUCCESS('Début de la génération des médias pour les projets...')
        )
        
        # Obtenir les projets à traiter
        if options.get('project_id'):
            try:
                projects = [Project.objects.get(id=options['project_id'])]
            except Project.DoesNotExist:
                raise CommandError(f"Projet avec l'ID {options['project_id']} introuvable")
        else:
            projects = Project.objects.all()
        
        # Traiter les projets en utilisant le service
        stats = ProjectMediaService.bulk_generate_media_for_projects(
            projects=projects,
            count=options.get('count', 1),
            source=options.get('source', 'generated')
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Génération terminée pour {len(projects)} projet(s):\n'
                f'  - Traités: {stats["processed"]}\n'
                f'  - Réussis: {stats["success"]}\n'
                f'  - Erreurs: {stats["errors"]}\n'
                f'  - Total médias créés: {stats["total_media"]}'
            )
        )
    
 