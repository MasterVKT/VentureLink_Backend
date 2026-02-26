#!/usr/bin/env python
"""
Script de génération de 25+ projets de démo pour VentureLink
"""
import os
import sys
import django
from decimal import Decimal
import random

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory, ProjectTag
from apps.projects.models.project_media import ProjectMedia

# Données de test
CATEGORIES = {
    'TECH': {'name_fr': 'Technologie', 'name_en': 'Technology'},
    'FINTECH': {'name_fr': 'Finance', 'name_en': 'Finance'},
    'HEALTH': {'name_fr': 'Santé', 'name_en': 'Health'},
    'EDTECH': {'name_fr': 'Éducation', 'name_en': 'Education'},
    'ECOMMERCE': {'name_fr': 'E-commerce', 'name_en': 'E-commerce'},
    'AGRITECH': {'name_fr': 'Agriculture', 'name_en': 'Agriculture'},
    'CLEANTECH': {'name_fr': 'Énergie Verte', 'name_en': 'Clean Energy'},
    'FOODTECH': {'name_fr': 'Alimentation', 'name_en': 'Food'},
}

TAGS = [
    'IA', 'Blockchain', 'Mobile', 'Web', 'SaaS', 'B2B', 'B2C',
    'Startup', 'Innovation', 'Digital', 'Cloud', 'IoT', 'Big Data',
    'Machine Learning', 'Cybersécurité', 'Fintech', 'Healthtech',
    'Edtech', 'E-commerce', 'Marketplace', 'Réseau Social'
]

STAGES = [
    Project.STAGE_IDEA,
    Project.STAGE_PROTOTYPE,
    Project.STAGE_DEVELOPMENT,
    Project.STAGE_GROWTH,
]

LOCATIONS = [
    ('France', 'Paris'),
    ('France', 'Lyon'),
    ('France', 'Marseille'),
    ('USA', 'New York'),
    ('USA', 'San Francisco'),
    ('UK', 'London'),
    ('Germany', 'Berlin'),
    ('Canada', 'Montreal'),
    ('Cameroon', 'Douala'),
    ('Cameroon', 'Yaoundé'),
    ('Senegal', 'Dakar'),
    ('Côte d\'Ivoire', 'Abidjan'),
]

PROJECT_TITLES = [
    "Plateforme IA pour l'analyse médicale",
    "Application de gestion financière personnelle",
    "Marketplace B2B pour professionnels",
    "Solution de cybersécurité pour PME",
    "Réseau social professionnel africain",
    "Plateforme e-learning interactive",
    "Application de livraison de repas locaux",
    "Solution IoT pour l'agriculture intelligente",
    "Marketplace de produits artisanaux",
    "Plateforme de télémedicine",
    "Application de covoiturage urbain",
    "Solution de paiement mobile",
    "Plateforme de recrutement par IA",
    "Application de suivi de fitness",
    "Marketplace de services à domicile",
    "Solution de gestion de stock",
    "Plateforme de crowdfunding",
    "Application de voyage personnalisé",
    "Solution RH pour startups",
    "Plateforme de streaming éducatif",
    "Application de meditation et bien-être",
    "Marketplace de mode éthique",
    "Solution de tracking logistique",
    "Plateforme de matching investisseurs",
    "Application de gestion de budget",
    "Solution d'automatisation marketing",
    "Plateforme de vente aux enchères",
    "Application de rencontre professionnelle",
    "Solution de monitoring serveur",
    "Plateforme de cours en ligne",
]

PROJECT_DESCRIPTIONS = [
    "Une solution innovante qui révolutionne le secteur grâce à l'intelligence artificielle et au machine learning.",
    "Notre plateforme connecte directement les professionnels avec leurs clients finaux.",
    "Une application mobile intuitive qui simplifie la vie quotidienne de millions d'utilisateurs.",
    "Notre technologie brevetée permet des gains de productivité de plus de 300%.",
    "Une solution complète qui répond aux défis majeurs du marché actuel.",
    "Notre équipe d'experts a développé un algorithme unique au monde.",
    "Une plateforme scalable capable de gérer des millions d'utilisateurs simultanés.",
    "Notre produit a déjà séduit plus de 1000 utilisateurs en phase bêta.",
    "Une innovation de rupture qui change les règles du jeu.",
    "Notre solution est déjà utilisée par plusieurs entreprises du Fortune 500.",
]


def get_or_create_user(email, first_name, last_name):
    """Crée ou récupère un utilisateur"""
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'password': 'pbkdf2_sha256$260000$dummy$dummy=',  # Mot de passe factice
        }
    )
    return user


def get_or_create_categories():
    """Crée les catégories si elles n'existent pas"""
    categories = {}
    for key, data in CATEGORIES.items():
        cat, _ = ProjectCategory.objects.get_or_create(
            name_fr=data['name_fr'],
            defaults={'name_en': data['name_en']}
        )
        categories[key] = cat
    return categories


def get_or_create_tags():
    """Crée les tags si elles n'existent pas"""
    tag_objects = {}
    for tag_name in TAGS:
        tag, _ = ProjectTag.objects.get_or_create(
            name_fr=tag_name,
            defaults={'name_en': tag_name}
        )
        tag_objects[tag_name] = tag
    return tag_objects


def generate_projects(num_projects=30):
    """Génère des projets de démo"""
    print(f"Generation de {num_projects} projets de demo...")
    
    # Récupérer ou créer les catégories et tags
    categories = get_or_create_categories()
    tags = get_or_create_tags()
    tag_keys = list(tags.keys())
    
    # Créer des utilisateurs entrepreneurs
    entrepreneurs = []
    for i in range(10):
        user = get_or_create_user(
            f'entrepreneur{i}@venturelink.com',
            f'Entrepreneur{i}',
            f'Test{i}',
        )
        entrepreneurs.append(user)
    
    # Créer des projets
    projects_created = []
    for i in range(num_projects):
        title = PROJECT_TITLES[i % len(PROJECT_TITLES)]
        if i >= len(PROJECT_TITLES):
            title = f"{title} {i // len(PROJECT_TITLES) + 1}"
        
        category_key = random.choice(list(categories.keys()))
        category = categories[category_key]
        
        entrepreneur = random.choice(entrepreneurs)
        location = random.choice(LOCATIONS)
        
        funding_min = Decimal(random.randint(10000, 50000))
        funding_max = Decimal(random.randint(50000, 500000))
        
        # Description
        short_desc = PROJECT_DESCRIPTIONS[random.randint(0, len(PROJECT_DESCRIPTIONS) - 1)]
        full_desc = f"""
# {title}

## Description du Projet

{short_desc}

## Notre Vision

Nous croyons en un avenir où la technologie permet à chacun de réaliser ses ambitions.
Notre solution apporte une réponse concrète aux problèmes rencontrés par nos utilisateurs.

## Le Marché

Le marché adressable représente plus de 10 milliards d'euros avec une croissance annuelle de 15%.

## Notre Équipe

Une équipe passionnée et expérimentée, issue des meilleures écoles et entreprises du secteur.

## Nos Objectifs

- Atteindre 100 000 utilisateurs d'ici fin 2026
- Développer de nouvelles fonctionnalités innovantes
- S'étendre à l'international
"""
        
        project = Project.objects.create(
            creator=entrepreneur,
            title=title,
            short_description=short_desc[:200],
            full_description=full_desc,
            category=category,
            stage=random.choice(STAGES),
            funding_min=funding_min,
            funding_max=funding_max,
            funding_currency='EUR',
            location_country=location[0],
            location_city=location[1],
            is_draft=False,
            status='ACTIVE',
            is_premium=random.choice([True, False, False, False]),  # 25% premium
            is_featured=random.choice([True, False, False, False, False]),  # 20% featured
            is_verified=random.choice([True, False, False]),  # 33% verified
            views_count=random.randint(0, 5000),
            interests_count=random.randint(0, 200),
            favorites_count=random.randint(0, 100),
        )
        
        # Ajouter des tags (2-5 tags par projet)
        num_tags = random.randint(2, 5)
        selected_tags = random.sample(tag_keys, num_tags)
        for tag_key in selected_tags:
            project.tags.add(tags[tag_key])
        
        projects_created.append(project)
        
        # Progress indicator
        if (i + 1) % 5 == 0:
            print(f"  OK {i + 1}/{num_projects} projets crees...")
    
    print(f"\nOK {len(projects_created)} projets crees avec succes !")
    return projects_created


def print_summary(projects):
    """Affiche un résumé des projets créés"""
    print("\n" + "="*60)
    print("RESUME DES PROJETS CREES")
    print("="*60)
    
    # Par catégorie
    print("\nPar Categorie:")
    for cat in ProjectCategory.objects.all():
        count = Project.objects.filter(category=cat, is_draft=False).count()
        if count > 0:
            print(f"  - {cat.name_fr}: {count} projets")
    
    # Par stade
    print("\nPar Stade:")
    for stage, label in Project.STAGE_CHOICES:
        count = Project.objects.filter(stage=stage, is_draft=False).count()
        if count > 0:
            print(f"  - {label}: {count} projets")
    
    # Par localisation
    print("\nPar Localisation:")
    locations = Project.objects.filter(is_draft=False).values('location_country').distinct()
    for loc in locations:
        count = Project.objects.filter(location_country=loc['location_country'], is_draft=False).count()
        print(f"  - {loc['location_country']}: {count} projets")
    
    # Stats globales
    print("\nStatistiques Globales:")
    print(f"  - Total projets: {Project.objects.filter(is_draft=False).count()}")
    print(f"  - Projets Premium: {Project.objects.filter(is_premium=True, is_draft=False).count()}")
    print(f"  - Projets Featured: {Project.objects.filter(is_featured=True, is_draft=False).count()}")
    print(f"  - Projets Verifies: {Project.objects.filter(is_verified=True, is_draft=False).count()}")
    
    total_funding = Project.objects.filter(is_draft=False).aggregate(
        total_min=models.Sum('funding_min'),
        total_max=models.Sum('funding_max')
    )
    print(f"\nTotal financement min: {total_funding['total_min'] or 0:,.0f} EUR")
    print(f"Total financement max: {total_funding['total_max'] or 0:,.0f} EUR")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    from django.db import models
    
    try:
        projects = generate_projects(30)
        print_summary(projects)
        print("\nVous pouvez maintenant tester l'application avec ces projets !")
        print("\nEndpoints API a tester:")
        print("  - GET /api/v1/projects/ - Liste des projets")
        print("  - GET /api/v1/projects/?category=technologie - Filtrer par categorie")
        print("  - GET /api/v1/projects/?search=IA - Recherche textuelle")
        print("  - GET /api/v1/projects/trending/ - Projets tendance")
        print("  - GET /api/v1/projects/featured/ - Projets en vedette")
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
