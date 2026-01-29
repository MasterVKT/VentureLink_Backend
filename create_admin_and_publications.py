#!/usr/bin/env python3
"""
Script Django pour créer un admin et des publications de test
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.content.models import Publication

User = get_user_model()

def make_user_admin():
    """Donner les permissions d'admin à l'utilisateur"""
    try:
        user = User.objects.get(email="admin@venturelink.com")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"✅ Utilisateur {user.email} est maintenant administrateur")
        return user
    except User.DoesNotExist:
        print("❌ Utilisateur admin@venturelink.com non trouvé")
        return None

def create_test_publications(admin_user):
    """Créer des publications de test"""
    publications_data = [
        {
            "title": "10 conseils pour réussir son pitch d'investisseur",
            "summary": "Découvrez les clés pour convaincre les investisseurs lors de votre présentation",
            "content": "Contenu complet de l'article avec tous les détails, conseils pratiques, exemples concrets...",
            "publication_type": "TIPS",
            "domain": "FINANCE_INVESTMENT",
            "tags": "pitch,investissement,conseils,startup",
            "status": "PUBLISHED",
            "is_featured": True,
            "allow_comments": True,
            "meta_description": "Guide complet pour réussir son pitch d'investisseur avec 10 conseils pratiques"
        },
        {
            "title": "Guide complet du business plan",
            "summary": "Apprenez à rédiger un business plan efficace",
            "content": "Un business plan est un document essentiel pour tout entrepreneur...",
            "publication_type": "TUTORIAL",
            "domain": "BUSINESS_STRATEGY",
            "tags": "business plan,stratégie,guide,entrepreneur",
            "status": "PUBLISHED",
            "is_featured": True,
            "allow_comments": True,
            "meta_description": "Guide complet pour rédiger un business plan efficace"
        },
        {
            "title": "Les tendances de l'entrepreneuriat en 2024",
            "summary": "Découvrez les nouvelles tendances qui façonnent l'entrepreneuriat",
            "content": "L'année 2024 marque un tournant dans l'entrepreneuriat...",
            "publication_type": "NEWS",
            "domain": "ENTREPRENEURSHIP",
            "tags": "tendances,2024,entrepreneuriat,innovation",
            "status": "PUBLISHED",
            "is_featured": False,
            "allow_comments": True,
            "meta_description": "Les principales tendances entrepreneuriales de 2024"
        },
        {
            "title": "Comment financer votre startup",
            "summary": "Les différentes options de financement pour les startups",
            "content": "Le financement est l'un des défis majeurs pour les entrepreneurs...",
            "publication_type": "EDUCATIONAL",
            "domain": "FINANCE_INVESTMENT",
            "tags": "financement,startup,investissement,capital",
            "status": "PUBLISHED",
            "is_featured": True,
            "allow_comments": True,
            "meta_description": "Guide complet des options de financement pour startups"
        },
        {
            "title": "L'importance du networking en entrepreneuriat",
            "summary": "Construire un réseau professionnel solide pour réussir",
            "content": "Le networking est essentiel pour tout entrepreneur qui souhaite réussir...",
            "publication_type": "TIPS",
            "domain": "NETWORKING",
            "tags": "networking,réseau,contacts,entrepreneuriat",
            "status": "PUBLISHED",
            "is_featured": False,
            "allow_comments": True,
            "meta_description": "L'art du networking pour entrepreneurs"
        }
    ]
    
    created_count = 0
    for pub_data in publications_data:
        try:
            publication = Publication.objects.create(
                author=admin_user,
                **pub_data
            )
            created_count += 1
            print(f"✅ Publication créée: {publication.title}")
        except Exception as e:
            print(f"❌ Erreur création publication: {e}")
    
    print(f"📊 {created_count}/{len(publications_data)} publications créées")

def main():
    """Fonction principale"""
    print("🚀 Configuration de l'admin et création des publications")
    print("=" * 60)
    
    # Étape 1: Donner les permissions d'admin
    admin_user = make_user_admin()
    if not admin_user:
        print("❌ Impossible de configurer l'administrateur")
        return
    
    # Étape 2: Créer les publications
    create_test_publications(admin_user)
    
    print("=" * 60)
    print("✅ Configuration terminée!")
    print(f"🌐 Vous pouvez maintenant tester l'application Flutter")
    print(f"👤 Admin: admin@venturelink.com / admin123")
    print(f"🔗 Interface admin: http://localhost:8000/admin/")

if __name__ == "__main__":
    main() 