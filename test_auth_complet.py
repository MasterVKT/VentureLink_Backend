#!/usr/bin/env python3
"""
Test complet d'authentification
"""

import os
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print("=" * 70)
print("🧪 TEST D'AUTHENTIFICATION - VENTURELINK")
print("=" * 70)

# 1. Vérifier l'utilisateur
print("\n1️⃣ VÉRIFICATION DE L'UTILISATEUR...")
print("-" * 70)

email = "admin@venturelink.com"
password = "Admin123!"

try:
    user = User.objects.get(email=email)
    print(f"✅ Utilisateur trouvé: {user.email}")
    print(f"   ID: {user.id}")
    print(f"   Nom: {user.first_name} {user.last_name}")
    print(f"   Actif: {user.is_active}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    print(f"   Vérifié: {user.is_verified}")
except User.DoesNotExist:
    print(f"❌ Utilisateur '{email}' non trouvé!")
    print("\nExécutez : python create_superuser.py")
    input("\nAppuyez sur Entrée...")
    sys.exit(1)

# 2. Vérifier le mot de passe
print("\n2️⃣ VÉRIFICATION DU MOT DE PASSE...")
print("-" * 70)

if user.check_password(password):
    print(f"✅ Mot de passe correct")
else:
    print(f"❌ Mot de passe incorrect!")
    print("\nPour réinitialiser :")
    print("  python manage.py shell")
    print("  >>> user = User.objects.get(email='admin@venturelink.com')")
    print("  >>> user.set_password('Admin123!')")
    print("  >>> user.save()")
    input("\nAppuyez sur Entrée...")
    sys.exit(1)

# 3. Générer les tokens JWT
print("\n3️⃣ GÉNÉRATION DES TOKENS JWT...")
print("-" * 70)

try:
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print(f"✅ Tokens générés avec succès")
    print(f"\n   Access Token (début):")
    print(f"   {access_token[:60]}...")
    print(f"\n   Refresh Token (début):")
    print(f"   {refresh_token[:60]}...")
except Exception as e:
    print(f"❌ Erreur: {e}")
    input("\nAppuyez sur Entrée...")
    sys.exit(1)

# 4. Vérifier les projets
print("\n4️⃣ VÉRIFICATION DES PROJETS...")
print("-" * 70)

try:
    from apps.projects.models import Project
    
    total = Project.objects.count()
    print(f"📊 Total projets: {total}")
    
    # Projets de cet utilisateur
    user_projects = Project.objects.filter(creator_id=user.id).count()
    print(f"📊 Vos projets: {user_projects}")
    
    # Afficher les projets
    projects = Project.objects.all()[:5]
    if projects.exists():
        print(f"\n📋 DERNIERS PROJETS:")
        for proj in projects:
            print(f"\n   • {proj.title}")
            try:
                print(f"     Statut: {proj.status}")
            except:
                pass
            try:
                print(f"     Objectif: {proj.funding_max} {proj.funding_currency}")
            except:
                pass
except Exception as e:
    print(f"⚠️  Projects: {e}")

# 5. Instructions de connexion
print("\n" + "=" * 70)
print("📋 INSTRUCTIONS DE CONNEXION")
print("=" * 70)

print("\n1️⃣ Lancez le serveur Django:")
print("   cd c:\\Users\\USER\\VentureLink\\VentureLink_BackEnd")
print("   venv\\Scripts\\activate")
print("   python manage.py runserver")

print("\n2️⃣ Dans l'application Flutter:")
print(f"   Email:    {email}")
print(f"   Password: {password}")

print("\n3️⃣ Interface Admin Django:")
print("   http://127.0.0.1:8000/admin/")

print("\n4️⃣ Test API avec curl:")
print("   curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \\")
print("     -H \"Content-Type: application/json\" \\")
print(f"     -d '{{\"email\":\"{email}\",\"password\":\"{password}\"}}'")

print("\n" + "=" * 70)
print("✅ TOUT EST PRÊT POUR LA CONNEXION !")
print("=" * 70)
print("\nAppuyez sur Entrée pour quitter...")

try:
    input()
except:
    pass
