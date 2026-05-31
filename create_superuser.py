#!/usr/bin/env python3
"""
Script pour créer un compte superutilisateur VentureLink
"""

import os
import sys

# IMPORTANT: Utiliser le bon chemin vers settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')

# Ajouter le chemin du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    """Créer un compte superutilisateur"""
    
    email = "admin@venturelink.com"
    password = "Admin123!"
    first_name = "Admin"
    last_name = "VentureLink"
    
    print("=" * 60)
    print("🔧 Création du compte superutilisateur VentureLink")
    print("=" * 60)
    
    try:
        # Vérifier si l'utilisateur existe déjà
        user = User.objects.get(email=email)
        print(f"\n⚠️  L'utilisateur {email} existe déjà!")
        
        # Mettre à jour les permissions
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        
        # Réinitialiser le mot de passe
        user.set_password(password)
        user.save()
        
        print(f"✅ Permissions administrateur mises à jour")
        print(f"✅ Mot de passe réinitialisé")
        
    except User.DoesNotExist:
        # Créer le superutilisateur
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        print(f"\n✅ Superutilisateur créé avec succès!")
    
    print("\n" + "=" * 60)
    print("📋 INFORMATIONS DE CONNEXION")
    print("=" * 60)
    print(f"👤 Email:    {email}")
    print(f"🔑 Mot de passe: {password}")
    print("=" * 60)
    
    # Vérifier la base de données
    print("\n📊 STATISTIQUES:")
    print(f"   Utilisateurs: {User.objects.count()}")
    
    try:
        from apps.projects.models import Project
        print(f"   Projets: {Project.objects.count()}")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ Script terminé!")
    print("=" * 60)
    
    return user

if __name__ == "__main__":
    try:
        create_superuser()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("\nVérifiez que:")
        print("  1. PostgreSQL est en cours d'exécution")
        print("  2. Les migrations sont appliquées")
        print("  3. Le virtual environment est activé")
        input("\nAppuyez sur Entrée pour quitter...")
