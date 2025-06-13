#!/usr/bin/env python
"""
Script de test pour les nouvelles API de limites de médias.
"""
import requests
import json

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
PROJECT_ID = '90d28f49-2b56-48af-92f8-90b01c9590a8'  # ID du premier projet

def test_media_limits_api():
    """Test de l'API des limites de médias."""
    print("🔗 Test de l'API des limites de médias")
    print("=" * 50)
    
    # URL de l'endpoint
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/media/limits/"
    
    print(f"📡 Tentative de requête à: {url}")
    
    try:
        # Faire la requête sans authentification (pour tester)
        response = requests.get(url, timeout=10)
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Réponse JSON reçue:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        elif response.status_code == 403:
            print("🔒 Erreur 403: Authentification requise (comportement attendu)")
            print("   → L'endpoint nécessite une authentification")
            
        elif response.status_code == 404:
            print("❌ Erreur 404: Endpoint non trouvé")
            print("   → Vérifiez que l'URL est correcte")
            
        else:
            print(f"⚠️ Statut inattendu: {response.status_code}")
            print(f"   Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion: Le serveur Django n'est pas démarré")
        print("   → Démarrez le serveur avec: python manage.py runserver")
        
    except requests.exceptions.Timeout:
        print("⏱️ Timeout: Le serveur met trop de temps à répondre")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

def test_project_media_endpoint():
    """Test de l'endpoint principal des médias."""
    print(f"\n🔗 Test de l'endpoint des médias de projet")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/media/"
    
    print(f"📡 Tentative de requête à: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"📊 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Nombre de médias: {len(data)}")
            if data:
                print("📸 Premier média:")
                first_media = data[0]
                print(f"   ID: {first_media.get('id', 'N/A')}")
                print(f"   Titre: {first_media.get('title', 'N/A')}")
                print(f"   Type: {first_media.get('media_type', 'N/A')}")
                print(f"   Principal: {first_media.get('is_primary', 'N/A')}")
                
        elif response.status_code == 403:
            print("🔒 Erreur 403: Authentification requise (comportement attendu)")
            
        else:
            print(f"⚠️ Statut: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == '__main__':
    test_media_limits_api()
    test_project_media_endpoint()
    print(f"\n✅ Tests des API terminés !") 