#!/usr/bin/env python3
"""
Script de test rapide pour vérifier l'authentification
Exécution : python test_auth_quick.py
"""

import os
import sys
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def test_auth():
    """Tester l'authentification"""
    
    print("=" * 60)
    print("🧪 TEST RAPIDE - Authentification VentureLink")
    print("=" * 60)
    
    email = "admin@venturelink.com"
    password = "Admin123!"
    
    # Étape 1 : Vérifier si l'utilisateur existe
    print("\n1️⃣ Vérification de l'utilisateur...")
    try:
        user = User.objects.get(email=email)
        print(f"   ✅ Utilisateur trouvé: {user.email}")
        print(f"      - Actif: {user.is_active}")
        print(f"      - Staff: {user.is_staff}")
        print(f"      - Superuser: {user.is_superuser}")
        print(f"      - Vérifié: {user.is_verified}")
    except User.DoesNotExist:
        print(f"   ❌ Utilisateur '{email}' non trouvé!")
        print("\n   Solution : Exécutez 'python create_superuser.py'")
        return False
    
    # Étape 2 : Vérifier le mot de passe
    print("\n2️⃣ Vérification du mot de passe...")
    if user.check_password(password):
        print(f"   ✅ Mot de passe correct")
    else:
        print(f"   ❌ Mot de passe incorrect!")
        print(f"\n   Solution : Réinitialiser avec user.set_password('{password}')")
        return False
    
    # Étape 3 : Générer un token JWT
    print("\n3️⃣ Génération du token JWT...")
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        print(f"   ✅ Token généré avec succès")
        print(f"      Access token (début): {access_token[:50]}...")
        print(f"      Refresh token (début): {refresh_token[:50]}...")
    except Exception as e:
        print(f"   ❌ Erreur génération token: {e}")
        return False
    
    # Étape 4 : Vérifier les projets de l'utilisateur
    print("\n4️⃣ Vérification des projets...")
    try:
        from apps.projects.models import Project
        
        # Tous les projets
        total_projects = Project.objects.count()
        print(f"   📊 Total projets dans la base: {total_projects}")
        
        # Projets de l'utilisateur
        user_projects = Project.objects.filter(creator=user).count()
        print(f"   📊 Vos projets: {user_projects}")
        
        # Projects récents
        recent = Project.objects.order_by('-created_at')[:3]
        if recent.exists():
            print(f"\n   📋 Derniers projets:")
            for proj in recent:
                print(f"      • {proj.title}")
                print(f"        Statut: {proj.status}")
                print(f"        Objectif: {proj.funding_max} {proj.funding_currency}")
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier les projets: {e}")
    
    # Étape 5 : Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Utilisateur: {email}")
    print(f"✅ Mot de passe: {password}")
    print(f"✅ Token JWT: Généré")
    print(f"✅ Prêt pour la connexion!")
    print("=" * 60)
    
    print("\n💡 COMMENT VOUS CONNECTER :")
    print("\n1. Dans l'application Flutter :")
    print("   - Email:    admin@venturelink.com")
    print("   - Password: Admin123!")
    print("\n2. Via API (Postman/curl) :")
    print("   POST http://127.0.0.1:8000/api/v1/auth/token/")
    print("   Body: {\"email\": \"admin@venturelink.com\", \"password\": \"Admin123!\"}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_auth()
        if success:
            print("\n✅ TEST RÉUSSI - Vous pouvez vous connecter!\n")
            sys.exit(0)
        else:
            print("\n❌ TEST ÉCHOUÉ - Suivez les instructions ci-dessus\n")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        print("Assurez-vous que:")
        print("  1. Le virtual environment est activé")
        print("  2. La base de données PostgreSQL est en cours d'exécution")
        print("  3. Les migrations ont été appliquées")
        sys.exit(1)
