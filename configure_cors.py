#!/usr/bin/env python3
"""
Script pour configurer CORS automatiquement
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import django
django.setup()

from django.conf import settings

print("=" * 70)
print("🔧 CONFIGURATION CORS - VENTURELINK")
print("=" * 70)

# Chemin du fichier settings.py
settings_file = os.path.join(BASE_DIR, 'venture_link_project', 'settings.py')

print(f"\n📄 Fichier à modifier : {settings_file}")

print("\n" + "=" * 70)
print("INSTRUCTIONS MANUELLES")
print("=" * 70)

print("""
1. Ouvrez le fichier :
   c:\\Users\\USER\\VentureLink\\VentureLink_BackEnd\\venture_link_project\\settings.py

2. Ajoutez 'corsheaders' dans INSTALLED_APPS :

   INSTALLED_APPS = [
       ...
       'corsheaders',  # ← Ajoutez cette ligne
       ...
   ]

3. Ajoutez le middleware CORS dans MIDDLEWARE :

   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',  # ← En PREMIER, avant CommonMiddleware
       'django.middleware.common.CommonMiddleware',
       ...
   ]

4. Ajoutez ces lignes à la fin du fichier :

   # Configuration CORS pour Flutter Web
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
       "http://localhost:50000",  # Flutter Web Chrome
       "http://127.0.0.1:50000",
       "http://localhost:52943",  # Port dynamique Flutter
   ]

   CORS_ALLOW_CREDENTIALS = True

   CORS_ALLOW_ALL_ORIGINS = True  # ← Pour le développement uniquement!

5. Sauvegardez le fichier

6. Redémarrez le serveur Django :
   - Ctrl+C pour arrêter
   - python manage.py runserver pour redémarrer
""")

print("\n" + "=" * 70)
print("VÉRIFICATION")
print("=" * 70)

# Vérifier si django-cors-headers est installé
try:
    import corsheaders
    print("✅ django-cors-headers est installé")
except ImportError:
    print("❌ django-cors-headers N'EST PAS installé")
    print("\nInstallez-le avec :")
    print("   venv\\Scripts\\activate")
    print("   pip install django-cors-headers")

print("\n" + "=" * 70)
input("Appuyez sur Entrée pour quitter...")
