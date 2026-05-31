"""
Script pour générer 30 projets de test VentureLink
Exécution : python generate_test_projects.py
(depuis le dossier VentureLink_BackEnd, avec le venv activé)
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal
from apps.projects.models import Project
from apps.users.models import User

# ─── Données des 30 projets ───────────────────────────────────────────────────

PROJECTS = [
    {
        "title": "AgroTech Cameroun",
        "description": "Plateforme numérique connectant les agriculteurs aux marchés locaux et internationaux via une application mobile. Solution innovante pour réduire les pertes post-récolte.",
        "funding_goal": 50000,
        "funding_current": 12000,
        "category": "Agriculture",
        "stage": "seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": False,
    },
    {
        "title": "SolarHome Africa",
        "description": "Kits solaires abordables pour l'électrification des ménages ruraux en Afrique subsaharienne. Modèle de paiement mobile en tranches adaptées aux revenus locaux.",
        "funding_goal": 120000,
        "funding_current": 45000,
        "category": "Énergie",
        "stage": "series_a",
        "location": "Douala, Cameroun",
        "is_premium": True,
    },
    {
        "title": "EduConnect",
        "description": "Application d'apprentissage hors ligne pour les zones sans connexion internet. Contenu scolaire téléchargeable couvrant le primaire et le secondaire.",
        "funding_goal": 30000,
        "funding_current": 8500,
        "category": "Éducation",
        "stage": "pre_seed",
        "location": "Bafoussam, Cameroun",
        "is_premium": False,
    },
    {
        "title": "HealthTrack Pro",
        "description": "Dossier médical électronique pour les cliniques rurales africaines. Suivi des patients, gestion des stocks de médicaments et télémédecine intégrée.",
        "funding_goal": 75000,
        "funding_current": 30000,
        "category": "Santé",
        "stage": "seed",
        "location": "Bamenda, Cameroun",
        "is_premium": True,
    },
    {
        "title": "WasteToWealth",
        "description": "Collecte et recyclage des déchets plastiques avec création d'emplois locaux. Transformation en matériaux de construction écologiques et abordables.",
        "funding_goal": 40000,
        "funding_current": 15000,
        "category": "Environnement",
        "stage": "seed",
        "location": "Douala, Cameroun",
        "is_premium": False,
    },
    {
        "title": "LogiExpress",
        "description": "Réseau de livraison last-mile optimisé pour l'Afrique centrale. Algorithme de routage adapté aux routes non goudronnées et aux adresses informelles.",
        "funding_goal": 90000,
        "funding_current": 22000,
        "category": "Logistique",
        "stage": "seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": False,
    },
    {
        "title": "FinanceMe",
        "description": "Microfinancement peer-to-peer pour les PME africaines exclues du système bancaire traditionnel. Scoring alternatif basé sur l'activité mobile money.",
        "funding_goal": 200000,
        "funding_current": 85000,
        "category": "Finance",
        "stage": "series_a",
        "location": "Abidjan, Côte d'Ivoire",
        "is_premium": True,
    },
    {
        "title": "ColdChain Solutions",
        "description": "Infrastructure frigorifique solaire pour la conservation des denrées alimentaires et médicaments. Réseau de hubs stratégiquement placés dans les marchés.",
        "funding_goal": 150000,
        "funding_current": 60000,
        "category": "Agriculture",
        "stage": "series_a",
        "location": "Garoua, Cameroun",
        "is_premium": True,
    },
    {
        "title": "TalentLink Africa",
        "description": "Plateforme de mise en relation entre talents africains qualifiés et entreprises internationales. Gestion des contrats et paiements en devises locales.",
        "funding_goal": 45000,
        "funding_current": 10000,
        "category": "Ressources Humaines",
        "stage": "pre_seed",
        "location": "Lagos, Nigeria",
        "is_premium": False,
    },
    {
        "title": "SmartFarm IoT",
        "description": "Capteurs IoT et IA pour l'agriculture de précision. Surveillance en temps réel de l'humidité, température et nutriments du sol. Alertes automatiques.",
        "funding_goal": 65000,
        "funding_current": 28000,
        "category": "Agriculture",
        "stage": "seed",
        "location": "Ngaoundéré, Cameroun",
        "is_premium": False,
    },
    {
        "title": "MobiPharma",
        "description": "Distribution de médicaments génériques de qualité via un réseau d'agents mobiles dans les zones rurales. Lutte contre les médicaments falsifiés.",
        "funding_goal": 55000,
        "funding_current": 18000,
        "category": "Santé",
        "stage": "seed",
        "location": "Maroua, Cameroun",
        "is_premium": False,
    },
    {
        "title": "BuildEasy",
        "description": "Marketplace de matériaux de construction locaux avec livraison. Mise en relation directe entre fabricants locaux et chantiers pour réduire les coûts.",
        "funding_goal": 35000,
        "funding_current": 9000,
        "category": "Construction",
        "stage": "pre_seed",
        "location": "Douala, Cameroun",
        "is_premium": False,
    },
    {
        "title": "GreenBus Electric",
        "description": "Transport urbain électrique écologique pour les grandes villes africaines. Flotte de minibus électriques rechargeables via panneaux solaires.",
        "funding_goal": 500000,
        "funding_current": 150000,
        "category": "Transport",
        "stage": "series_b",
        "location": "Nairobi, Kenya",
        "is_premium": True,
    },
    {
        "title": "AquaPure",
        "description": "Systèmes de purification d'eau décentralisés pour les communautés rurales. Maintenance simplifiée et modèle économique basé sur le pay-per-use.",
        "funding_goal": 80000,
        "funding_current": 35000,
        "category": "Eau & Assainissement",
        "stage": "seed",
        "location": "Ebolowa, Cameroun",
        "is_premium": False,
    },
    {
        "title": "FashionMade Africa",
        "description": "Plateforme e-commerce valorisant la mode africaine authentique. Connexion artisans et stylistes africains aux marchés de la diaspora mondiale.",
        "funding_goal": 25000,
        "funding_current": 7500,
        "category": "Mode & Artisanat",
        "stage": "pre_seed",
        "location": "Accra, Ghana",
        "is_premium": False,
    },
    {
        "title": "CyberShield Africa",
        "description": "Solutions de cybersécurité adaptées aux PME africaines. Formation, audit et protection contre les cyberattaques à prix accessibles.",
        "funding_goal": 70000,
        "funding_current": 25000,
        "category": "Technologie",
        "stage": "seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": True,
    },
    {
        "title": "LegalEasy",
        "description": "Accès simplifié aux services juridiques via une application mobile. Mise en relation avec des avocats, modèles de contrats et consultations vidéo.",
        "funding_goal": 20000,
        "funding_current": 6000,
        "category": "Services Juridiques",
        "stage": "pre_seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": False,
    },
    {
        "title": "TourismConnect",
        "description": "Plateforme de tourisme local connectant voyageurs et guides touristiques africains certifiés. Expériences authentiques et circuits personnalisés.",
        "funding_goal": 30000,
        "funding_current": 11000,
        "category": "Tourisme",
        "stage": "seed",
        "location": "Kribi, Cameroun",
        "is_premium": False,
    },
    {
        "title": "MediaHub Africa",
        "description": "Plateforme de streaming de contenus culturels africains (musique, films, séries). Monétisation directe pour les créateurs de contenu locaux.",
        "funding_goal": 100000,
        "funding_current": 40000,
        "category": "Média & Divertissement",
        "stage": "series_a",
        "location": "Douala, Cameroun",
        "is_premium": True,
    },
    {
        "title": "FoodTech Delivery",
        "description": "Service de livraison de repas de restaurants locaux avec optimisation IA des routes. Focus sur les quartiers périphériques non couverts par les concurrents.",
        "funding_goal": 45000,
        "funding_current": 16000,
        "category": "Restauration",
        "stage": "seed",
        "location": "Douala, Cameroun",
        "is_premium": False,
    },
    {
        "title": "SportAcademy Digital",
        "description": "Académie sportive digitale pour découvrir et former les jeunes talents africains. Coaching vidéo, suivi de performance et mise en relation avec les clubs.",
        "funding_goal": 35000,
        "funding_current": 12000,
        "category": "Sport",
        "stage": "seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": False,
    },
    {
        "title": "InsurTech Micro",
        "description": "Micro-assurance accessible via mobile pour les travailleurs informels africains. Couverture santé, accidents et récoltes avec primes à partir de 500 FCFA/mois.",
        "funding_goal": 180000,
        "funding_current": 70000,
        "category": "Assurance",
        "stage": "series_a",
        "location": "Dakar, Sénégal",
        "is_premium": True,
    },
    {
        "title": "CleanCook",
        "description": "Cuisinières à biogaz produites localement à partir de déchets organiques. Réduction de la déforestation et amélioration de la qualité de l'air intérieur.",
        "funding_goal": 60000,
        "funding_current": 22000,
        "category": "Énergie",
        "stage": "seed",
        "location": "Buea, Cameroun",
        "is_premium": False,
    },
    {
        "title": "AgriFinance",
        "description": "Financement des intrants agricoles avec remboursement après récolte. Partenariat avec coopératives agricoles et intégration du suivi satellite des cultures.",
        "funding_goal": 250000,
        "funding_current": 95000,
        "category": "Finance",
        "stage": "series_a",
        "location": "Bamako, Mali",
        "is_premium": True,
    },
    {
        "title": "PrintLocal",
        "description": "Service d'impression numérique à la demande pour les entrepreneurs africains. Emballages, flyers, banderoles avec livraison en 24h dans les grandes villes.",
        "funding_goal": 15000,
        "funding_current": 5000,
        "category": "Impression & Design",
        "stage": "pre_seed",
        "location": "Douala, Cameroun",
        "is_premium": False,
    },
    {
        "title": "TechTraining Hub",
        "description": "Centres de formation aux métiers du numérique dans les villes secondaires africaines. Développement web, data science et cybersécurité en langues locales.",
        "funding_goal": 85000,
        "funding_current": 32000,
        "category": "Éducation",
        "stage": "seed",
        "location": "Bafoussam, Cameroun",
        "is_premium": False,
    },
    {
        "title": "WomenBiz Platform",
        "description": "Écosystème d'accompagnement des femmes entrepreneures africaines. Mentorat, accès au financement, réseau et formations adaptées aux contraintes spécifiques.",
        "funding_goal": 40000,
        "funding_current": 18000,
        "category": "Social & Inclusion",
        "stage": "seed",
        "location": "Yaoundé, Cameroun",
        "is_premium": False,
    },
    {
        "title": "MapMyCity",
        "description": "Cartographie participative des villes africaines avec géolocalisation des services. Données ouvertes pour les collectivités et les entreprises de logistique.",
        "funding_goal": 55000,
        "funding_current": 20000,
        "category": "Technologie",
        "stage": "seed",
        "location": "Kinshasa, RDC",
        "is_premium": False,
    },
    {
        "title": "CryptoRemit",
        "description": "Transferts d'argent internationaux via blockchain pour la diaspora africaine. Frais réduits à 1% contre 7-10% pour les opérateurs traditionnels.",
        "funding_goal": 300000,
        "funding_current": 120000,
        "category": "Finance",
        "stage": "series_a",
        "location": "Douala, Cameroun",
        "is_premium": True,
    },
    {
        "title": "EcoPackaging",
        "description": "Production d'emballages biodégradables à partir de fibres végétales locales. Alternative écologique aux emballages plastiques pour l'industrie alimentaire.",
        "funding_goal": 70000,
        "funding_current": 26000,
        "category": "Environnement",
        "stage": "seed",
        "location": "Limbé, Cameroun",
        "is_premium": False,
    },
]

# ─── Création des projets ─────────────────────────────────────────────────────

def create_projects():
    # Récupère le premier superuser ou crée un utilisateur par défaut
    try:
        owner = User.objects.filter(is_superuser=True).first()
        if not owner:
            owner = User.objects.first()
        if not owner:
            print("❌ Aucun utilisateur trouvé. Crée d'abord un superuser avec:")
            print("   python manage.py createsuperuser")
            return
    except Exception as e:
        print(f"❌ Erreur utilisateur: {e}")
        return

    created = 0
    skipped = 0

    for p in PROJECTS:
        try:
            # Vérifie si le projet existe déjà
            if Project.objects.filter(title=p["title"]).exists():
                print(f"⏭️  Déjà existant : {p['title']}")
                skipped += 1
                continue

            Project.objects.create(
                title=p["title"],
                description=p["description"],
                funding_goal=Decimal(str(p["funding_goal"])),
                funding_current=Decimal(str(p["funding_current"])),
                location=p["location"],
                is_premium=p["is_premium"],
                owner=owner,
                status="active",
            )
            print(f"✅ Créé : {p['title']}")
            created += 1

        except Exception as e:
            print(f"❌ Erreur pour {p['title']}: {e}")

    print(f"\n🎉 Terminé ! {created} projets créés, {skipped} ignorés (déjà existants).")

if __name__ == "__main__":
    create_projects()
