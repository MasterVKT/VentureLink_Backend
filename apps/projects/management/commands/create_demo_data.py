import os
import random
import urllib.request
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.users.models import User, Profile
from apps.projects.models import (
    Project, ProjectCategory, ProjectTag, ProjectNeeds, ProjectSkillsNeeded, ProjectMedia, ProjectFavorite, ProjectInterest
)
from django.db import transaction
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

CITIES = ["Douala", "Yaoundé", "Garoua", "Bafoussam", "Maroua", "Bertoua", "Ngaoundéré", "Bamenda"]
SECTORS = [
    ("Agriculture", "Agroalimentaire, production végétale et animale"),
    ("FinTech", "Solutions financières et bancaires digitales"),
    ("Énergie", "Énergies renouvelables et accès à l'électricité"),
    ("Santé", "Services de santé et e-santé"),
    ("Éducation", "EdTech, formation professionnelle"),
    ("Transport", "Logistique et mobilité urbaine"),
    ("Commerce", "E-commerce, distribution locale"),
    ("Tourisme", "Tourisme et culture camerounaise"),
]
PROFILE_PICS = [
    "https://images.pexels.com/photos/614810/pexels-photo-614810.jpeg",  # homme
    "https://images.pexels.com/photos/1130626/pexels-photo-1130626.jpeg",  # femme
    "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg",  # homme
    "https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg",  # femme
]
PROJECT_IMAGES = [
    "https://images.pexels.com/photos/461382/pexels-photo-461382.jpeg",  # agriculture
    "https://images.pexels.com/photos/267614/pexels-photo-267614.jpeg",  # tech
    "https://images.pexels.com/photos/356056/pexels-photo-356056.jpeg",  # énergie
    "https://images.pexels.com/photos/3183197/pexels-photo-3183197.jpeg",  # santé
    "https://images.pexels.com/photos/256369/pexels-photo-256369.jpeg",  # éducation
    "https://images.pexels.com/photos/21014/pexels-photo.jpg",           # transport
    "https://images.pexels.com/photos/264636/pexels-photo-264636.jpeg",  # commerce
    "https://images.pexels.com/photos/417173/pexels-photo-417173.jpeg",  # tourisme
]

CATEGORY_DATA = [
    {"fr": "Agriculture", "en": "Agriculture"},
    {"fr": "Technologie financière", "en": "FinTech"},
    {"fr": "Énergie", "en": "Energy"},
    {"fr": "Santé", "en": "Health"},
    {"fr": "Éducation", "en": "Education"},
    {"fr": "Transport", "en": "Transport"},
    {"fr": "Commerce", "en": "Commerce"},
    {"fr": "Tourisme", "en": "Tourism"},
]

TAGS = [
    {"fr": "Innovation", "en": "Innovation"},
    {"fr": "Impact social", "en": "Social Impact"},
    {"fr": "Croissance", "en": "Growth"},
    {"fr": "Durabilité", "en": "Sustainability"},
    {"fr": "Jeunesse", "en": "Youth"},
    {"fr": "Femmes", "en": "Women"},
]

FIRST_NAMES = ["Arnaud", "Brice", "Clarisse", "Djamila", "Emmanuel", "Fatou", "Gaston", "Hortense"]
LAST_NAMES = ["Nana", "Mbarga", "Tchoumi", "Ngono", "Biloa", "Fouda", "Abega", "Essomba"]

@transaction.atomic
def download_image(url):
    temp_img = NamedTemporaryFile(suffix='.jpg')
    with urllib.request.urlopen(url) as u:
        temp_img.write(u.read())
    temp_img.flush()
    temp_img.seek(0)
    return temp_img

class Command(BaseCommand):
    help = "Crée des utilisateurs et projets factices pour les tests (contexte Cameroun)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Début de la génération de données de test..."))

        # 1. Créer les catégories si elles n'existent pas
        categories = []
        for cat in CATEGORY_DATA:
            obj, _ = ProjectCategory.objects.get_or_create(
                name_fr=cat["fr"],
                defaults={"name_en": cat["en"]}
            )
            categories.append(obj)

        # 2. Créer les tags si besoin
        tags = []
        for tag in TAGS:
            obj, _ = ProjectTag.objects.get_or_create(
                name_fr=tag["fr"],
                defaults={"name_en": tag["en"]}
            )
            tags.append(obj)

        # 3. Créer 3 utilisateurs de test (en plus de l'existant)
        users = list(User.objects.filter(email__startswith="testuser"))
        nb_to_create = 3 - len(users)
        for i in range(nb_to_create):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = f"testuser{i+1}@venturelink.cm"
            city = random.choice(CITIES)
            phone = f"+2376{random.randint(50,99)}{random.randint(100000,999999)}"
            pic_url = PROFILE_PICS[i % len(PROFILE_PICS)]
            user = User.objects.create_user(
                email=email,
                password="testpassword123",
                first_name=first,
                last_name=last,
                is_active=True,
                user_type="BOTH",
                phone_number=phone,
                location=city,
                language="fr",
                is_verified=True,
                preferred_currency=random.choice(["XAF", "EUR", "USD"]),
            )
            # Ajout photo de profil
            try:
                profile = Profile.objects.get(user=user)
                img_temp = download_image(pic_url)
                profile.photo.save(f"profile_{user.id}.jpg", File(img_temp), save=True)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Photo de profil non ajoutée: {e}"))
            users.append(user)

        # Ajouter l'utilisateur existant (s'il y en a un)
        all_users = list(User.objects.filter(is_active=True))
        for user in all_users:
            if user not in users:
                users.append(user)

        # 4. Créer 2 à 4 projets par utilisateur
        for user in users:
            nb_projects = random.randint(2, 4)
            for p in range(nb_projects):
                cat = random.choice(categories)
                sector, sector_desc = random.choice(SECTORS)
                title = f"{sector} au Cameroun - Projet {random.randint(100,999)}"
                short_desc = f"{sector_desc}. Localisé à {random.choice(CITIES)}."
                full_desc = (
                    f"Ce projet vise à développer des solutions innovantes dans le secteur {sector.lower()} au Cameroun. "
                    f"Notre objectif est d'avoir un impact positif sur la communauté locale, en favorisant l'emploi et la croissance durable.\n"
                    f"Description longue factice pour les tests.\n"
                    f"Contact: {user.email}"
                )
                project = Project.objects.create(
                    creator=user,
                    title=title,
                    short_description=short_desc,
                    full_description=full_desc,
                    category=cat,
                    stage=random.choice([c[0] for c in Project.STAGE_CHOICES]),
                    funding_min=random.randint(1000000, 5000000),
                    funding_max=random.randint(6000000, 20000000),
                    funding_currency=random.choice(["XAF", "EUR", "USD"]),
                    location_country="Cameroun",
                    location_city=random.choice(CITIES),
                    is_premium=random.choice([True, False]),
                    is_featured=random.choice([True, False]),
                    is_draft=False,
                    status=Project.STATUS_ACTIVE,
                    published_at=timezone.now(),
                )
                # Ajout tags
                project.tags.set(random.sample(tags, k=random.randint(1, 3)))
                # Ajout médias
                try:
                    img_url = random.choice(PROJECT_IMAGES)
                    img_temp = download_image(img_url)
                    ProjectMedia.objects.create(
                        project=project,
                        file=File(img_temp),
                        media_type="IMAGE",
                        title=f"Image projet {project.id}",
                        is_primary=True,
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Image projet non ajoutée: {e}"))
                # Ajout besoins
                ProjectNeeds.objects.create(
                    project=project,
                    resource_type=random.choice([c[0] for c in ProjectNeeds.RESOURCE_TYPE_CHOICES]),
                    title="Besoin de financement initial",
                    description="Recherche de fonds pour le démarrage du projet.",
                    amount=random.randint(500000, 2000000),
                    is_critical=True,
                )
                # Ajout compétences requises
                ProjectSkillsNeeded.objects.create(
                    project=project,
                    name="Gestion de projet",
                    description="Compétence en gestion de projet et planification.",
                    priority=random.choice([c[0] for c in ProjectSkillsNeeded.PRIORITY_CHOICES]),
                    required_level=random.randint(3, 5),
                )

        # 5. Générer des interactions (favoris et intérêts)
        all_projects = list(Project.objects.all())
        for user in users:
            # Exclure les projets créés par l'utilisateur
            other_projects = [p for p in all_projects if p.creator != user]
            # Favoris
            favs = random.sample(other_projects, k=min(2, len(other_projects)))
            for proj in favs:
                ProjectFavorite.objects.get_or_create(user=user, project=proj)
            # Intérêts
            interests = random.sample(other_projects, k=min(2, len(other_projects)))
            for proj in interests:
                ProjectInterest.objects.get_or_create(
                    user=user,
                    project=proj,
                    defaults={
                        "message": f"Je suis intéressé par ce projet ({proj.title}) pour un éventuel investissement.",
                        "status": ProjectInterest.STATUS_PENDING,
                        "is_anonymous": False,
                        "investment_amount": random.randint(100000, 1000000),
                        "investment_currency": proj.funding_currency,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Génération de données de test terminée.")) 