#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings.development')
django.setup()

from apps.projects.models import Project
from apps.users.models import User
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def get_jwt_token(user):
    """Génère un token JWT pour un utilisateur"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def test_media_generation_api():
    """Test l'API de génération de médias"""
    
    # Récupérer un projet et son créateur
    project = Project.objects.first()
    if not project:
        print("Aucun projet trouvé dans la base de données")
        return
    
    user = project.creator
    print(f"Test avec le projet: {project.title}")
    print(f"Créateur: {user.email}")
    
    # Créer un client API
    client = APIClient()
    
    # Obtenir un token JWT
    token = get_jwt_token(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # URL pour la génération de médias
    url = f'/api/v1/projects/{project.id}/media/generate/'
    
    # Test 1: Génération d'un média simple
    print("\n1. Test génération d'un média...")
    data = {
        'source': 'placeholder',
        'count': 1,
        'overwrite': True
    }
    
    response = client.post(url, data, format='json')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Succès: {result['message']}")
        print(f"Médias créés: {result['stats']['created']}")
    else:
        print(f"Erreur: {response.content}")
    
    # Test 2: Tentative de génération sans overwrite (devrait échouer)
    print("\n2. Test sans overwrite (devrait échouer)...")
    data['overwrite'] = False
    response = client.post(url, data, format='json')
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        result = response.json()
        print(f"Erreur attendue: {result['error']}")
    
    # Test 3: Génération avec source différente
    print("\n3. Test avec source 'generated'...")
    data = {
        'source': 'generated',
        'count': 2,
        'overwrite': True
    }
    response = client.post(url, data, format='json')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Succès: {result['message']}")
        print(f"Médias créés: {result['stats']['created']}")
        
        # Afficher les URLs des médias générés
        for media in result['media']:
            print(f"  - {media['title']}: {media['file']}")
    
    # Test 4: Lister les médias du projet
    print("\n4. Test listage des médias...")
    list_url = f'/api/v1/projects/{project.id}/media/'
    response = client.get(list_url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        media_list = response.json()
        print(f"Nombre de médias: {len(media_list)}")
        for media in media_list:
            print(f"  - {media['title']} (Principal: {media['is_primary']})")

def test_media_management():
    """Test la gestion des médias existants"""
    
    # Récupérer un projet avec des médias
    project = Project.objects.filter(media__isnull=False).first()
    if not project:
        print("Aucun projet avec médias trouvé")
        return
    
    user = project.creator
    client = APIClient()
    token = get_jwt_token(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Récupérer le premier média
    media = project.media.first()
    if not media:
        print("Aucun média trouvé pour le projet")
        return
    
    print(f"\nTest gestion du média: {media.title}")
    
    # Test 1: Définir comme principal
    if media.media_type == 'IMAGE':
        print("1. Test définition comme principal...")
        url = f'/api/v1/projects/{project.id}/media/{media.id}/set-primary/'
        response = client.post(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Succès: {result['message']}")
    
    # Test 2: Réorganisation des médias
    print("2. Test réorganisation...")
    media_list = list(project.media.all())
    if len(media_list) > 1:
        url = f'/api/v1/projects/{project.id}/media/reorder/'
        data = {
            'media_order': [
                {'id': str(media_list[0].id), 'order': 2},
                {'id': str(media_list[1].id), 'order': 1}
            ]
        }
        response = client.post(url, data, format='json')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Succès: {result['message']}")

if __name__ == "__main__":
    print("Test de l'API de gestion des médias de projets")
    print("=" * 60)
    
    try:
        test_media_generation_api()
        test_media_management()
        
        print("\n" + "=" * 60)
        print("Tests terminés !")
        
    except Exception as e:
        print(f"Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc() 