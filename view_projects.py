#!/usr/bin/env python3
"""
Voir vos projets dans la base de données
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import django
django.setup()

print("=" * 60)
print("📋 VOS PROJETS VENTURELINK")
print("=" * 60)

try:
    from apps.projects.models import Project
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Tous les projets
    all_projects = Project.objects.all()
    print(f"\n📊 Total projets: {all_projects.count()}\n")
    
    if all_projects.exists():
        print("─" * 60)
        for i, project in enumerate(all_projects, 1):
            print(f"\n{i}. {project.title}")
            print(f"   Description: {project.short_description[:100]}...")
            print(f"   Statut: {project.status}")
            print(f"   Étape: {project.stage}")
            print(f"   Objectif: {project.funding_max} {project.funding_currency}")
            print(f"   Collecté: {project.funding_min} {project.funding_currency}")
            print(f"   Créé par: {project.creator_name or 'Inconnu'}")
            print(f"   Date: {project.created_at}")
            print("─" * 60)
    else:
        print("❌ Aucun projet trouvé dans la base de données")
        
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 60)
input("Appuyez sur Entrée pour quitter...")
