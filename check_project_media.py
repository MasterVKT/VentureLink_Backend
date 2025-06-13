#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings.development')
django.setup()

from apps.projects.models import Project, ProjectMedia

def check_project_media():
    """Vérifie les médias associés aux projets"""
    projects = Project.objects.all()
    
    print(f"Vérification des médias pour {projects.count()} projets:")
    print("=" * 80)
    
    projects_with_media = 0
    total_media = 0
    
    for project in projects:
        media_count = project.media.count()
        if media_count > 0:
            projects_with_media += 1
            total_media += media_count
            
            print(f"\n📁 Projet: {project.title}")
            print(f"   ID: {project.id}")
            print(f"   Médias: {media_count}")
            
            for media in project.media.all():
                print(f"   📸 {media.title}")
                print(f"      - Type: {media.media_type}")
                print(f"      - Fichier: {media.file.name}")
                print(f"      - Principal: {'Oui' if media.is_primary else 'Non'}")
                print(f"      - Créé le: {media.created_at}")
    
    print("\n" + "=" * 80)
    print(f"Résumé:")
    print(f"- Projets avec médias: {projects_with_media}")
    print(f"- Projets sans médias: {projects.count() - projects_with_media}")
    print(f"- Total des médias: {total_media}")

if __name__ == "__main__":
    check_project_media() 