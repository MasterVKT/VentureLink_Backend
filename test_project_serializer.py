#!/usr/bin/env python
"""
Script de test pour vérifier la sérialisation des projets avec leurs médias.
"""
import os
import sys
import django

# Configuration de Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings.development')
django.setup()

from apps.projects.models.project import Project
from apps.projects.serializers.project_serializer import ProjectListSerializer
import json

def test_project_serialization():
    """Test la sérialisation des projets avec médias."""
    print("Test de la sérialisation des projets avec médias")
    print("=" * 60)
    
    # Récupérer les premiers projets avec leurs médias
    projects = Project.objects.select_related('category', 'creator').prefetch_related('media', 'tags')[:3]
    
    print(f"Nombre de projets trouvés: {projects.count()}")
    
    for project in projects:
        print(f"\n📁 Projet: {project.title}")
        print(f"   ID: {project.id}")
        print(f"   Médias count: {project.media.count()}")
        
        # Sérialiser le projet
        serializer = ProjectListSerializer(project)
        data = serializer.data
        
        print(f"   Primary image via property: {project.primary_image}")
        if project.primary_image:
            print(f"   Primary image file: {project.primary_image.file}")
            if project.primary_image.file:
                print(f"   Primary image URL: {project.primary_image.file.url}")
        
        print(f"   Primary image via serializer: {data.get('primary_image_url')}")
        
        # Afficher le JSON sérialisé (formaté)
        print("   JSON sérialisé:")
        print(json.dumps(data, indent=4, ensure_ascii=False, default=str))
        print("-" * 40)

if __name__ == "__main__":
    test_project_serialization() 