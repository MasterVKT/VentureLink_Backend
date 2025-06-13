#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings.development')
django.setup()

from apps.projects.models import Project, ProjectMedia

def list_projects():
    """Liste tous les projets existants"""
    projects = Project.objects.all()
    print(f"Nombre total de projets: {projects.count()}")
    print("\nProjets existants:")
    print("-" * 80)
    
    for project in projects:
        print(f"ID: {project.id}")
        print(f"Titre: {project.title}")
        print(f"Description courte: {project.short_description}")
        print(f"Catégorie: {project.category}")
        print(f"Créateur: {project.creator}")
        print(f"Stade: {project.stage}")
        print(f"Médias existants: {project.media.count()}")
        
        # Lister les médias existants
        if project.media.exists():
            print("  Médias:")
            for media in project.media.all():
                print(f"    - {media.title or 'Sans titre'} ({media.media_type})")
        else:
            print("  Aucun média associé")
        
        print("-" * 80)

if __name__ == "__main__":
    list_projects() 