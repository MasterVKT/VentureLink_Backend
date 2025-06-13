#!/usr/bin/env python
"""
Script de test pour les nouvelles fonctionnalités de limites de médias.
"""
import os
import sys
import django

# Configuration de Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings.development')
django.setup()

from apps.projects.services.project_media_service import ProjectMediaService
from apps.projects.models import Project
from apps.users.models import User

def test_media_limits():
    """Test les nouvelles fonctionnalités de limites de médias."""
    print("🧪 Test des limites de médias basées sur le statut premium")
    print("=" * 60)
    
    # Test des utilisateurs
    user_free = User.objects.filter(is_premium=False).first()
    user_premium = User.objects.filter(is_premium=True).first()
    
    print("👥 Utilisateurs de test:")
    if not user_free:
        print('❌ Aucun utilisateur gratuit trouvé')
        # Créer un utilisateur gratuit pour les tests
        user_free = User.objects.first()
        if user_free:
            user_free.is_premium = False
            user_free.save()
            print(f'✅ Utilisateur gratuit créé: {user_free.email}')
    else:
        print(f'✅ Utilisateur gratuit: {user_free.email}')
    
    if not user_premium:
        print('❌ Aucun utilisateur premium trouvé')
        # Simuler un utilisateur premium
        if user_free:
            print('   → Simulation avec un utilisateur premium')
            user_premium = user_free  # Pour la simulation
    else:
        print(f'✅ Utilisateur premium: {user_premium.email}')
    
    print(f'\n📊 Limites configurées:')
    print(f'   Utilisateurs gratuits: {ProjectMediaService.MAX_MEDIA_FREE_USER} média(s)')
    print(f'   Utilisateurs premium: {ProjectMediaService.MAX_MEDIA_PREMIUM_USER} média(s)')
    
    # Test des limites
    if user_free:
        limit_free = ProjectMediaService.get_user_media_limit(user_free)
        print(f'\n🆓 Limite utilisateur gratuit: {limit_free} média(s)')
    
    if user_premium:
        # Simuler premium
        user_premium.is_premium = True
        limit_premium = ProjectMediaService.get_user_media_limit(user_premium)
        print(f'💎 Limite utilisateur premium: {limit_premium} média(s)')
    
    # Test avec un projet réel
    project = Project.objects.first()
    if project and user_free:
        print(f'\n📁 Test avec le projet: "{project.title}"')
        print(f'   Médias actuels: {project.media.count()}')
        
        # Test utilisateur gratuit
        user_free.is_premium = False
        limits_free = ProjectMediaService.check_media_limit(project, user_free)
        print(f'\n🆓 Limites utilisateur gratuit:')
        print(f'   ✓ Peut ajouter: {limits_free["can_add"]}')
        print(f'   ✓ Limite: {limits_free["limit"]}')
        print(f'   ✓ Actuel: {limits_free["current"]}')
        print(f'   ✓ Restant: {limits_free["remaining"]}')
        print(f'   ✓ Premium: {limits_free["is_premium"]}')
        
        # Test utilisateur premium
        user_free.is_premium = True
        limits_premium = ProjectMediaService.check_media_limit(project, user_free)
        print(f'\n💎 Limites utilisateur premium:')
        print(f'   ✓ Peut ajouter: {limits_premium["can_add"]}')
        print(f'   ✓ Limite: {limits_premium["limit"]}')
        print(f'   ✓ Actuel: {limits_premium["current"]}')
        print(f'   ✓ Restant: {limits_premium["remaining"]}')
        print(f'   ✓ Premium: {limits_premium["is_premium"]}')
        
        # Restaurer l'état original
        user_free.is_premium = False
        user_free.save()

def test_compression_config():
    """Test la configuration de compression."""
    print(f'\n🖼️ Configuration de compression:')
    config = ProjectMediaService.COMPRESSION_CONFIG
    for name, settings in config.items():
        print(f'   {name}: qualité={settings["quality"]}, optimisé={settings["optimize"]}')

if __name__ == '__main__':
    test_media_limits()
    test_compression_config()
    print(f'\n✅ Tests terminés !') 