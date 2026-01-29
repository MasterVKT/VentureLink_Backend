"""
Commande Django pour créer des données de test pour les projets avec médias.
"""
import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from pathlib import Path

from apps.projects.models import Project, ProjectCategory, ProjectTag, ProjectMedia
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crée des données de test pour les projets avec différents types de médias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime toutes les données existantes avant de créer les nouvelles',
        )
        parser.add_argument(
            '--projects',
            type=int,
            default=8,
            help='Nombre de projets à créer (par défaut: 8)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            self.clear_data()

        self.stdout.write('🚀 Création des données de test...')
        
        # Créer les utilisateurs de test
        users = self.create_test_users()
        self.stdout.write(f'✅ {len(users)} utilisateurs créés')
        
        # Créer les catégories
        categories = self.create_categories()
        self.stdout.write(f'✅ {len(categories)} catégories créées')
        
        # Créer les tags
        tags = self.create_tags()
        self.stdout.write(f'✅ {len(tags)} tags créés')
        
        # Créer les projets avec médias
        projects = self.create_projects_with_media(users, categories, tags, options['projects'])
        self.stdout.write(f'✅ {len(projects)} projets créés avec médias')
        
        self.stdout.write(self.style.SUCCESS('🎉 Données de test créées avec succès!'))

    def clear_data(self):
        """Supprime toutes les données de test existantes"""
        ProjectMedia.objects.all().delete()
        Project.objects.all().delete()
        ProjectCategory.objects.all().delete()
        ProjectTag.objects.all().delete()
        User.objects.filter(email__contains='test.venturelink').delete()

    def create_test_users(self):
        """Crée des utilisateurs de test"""
        users = []
        
        user_data = [
            {
                'email': 'marie.entrepreneur@test.venturelink.com',
                'first_name': 'Marie',
                'last_name': 'Dubois',
                'user_type': 'PROJECT_OWNER',
                'location': 'Paris, France'
            },
            {
                'email': 'jean.investisseur@test.venturelink.com',
                'first_name': 'Jean',
                'last_name': 'Martin',
                'user_type': 'INVESTOR',
                'location': 'Lyon, France',
                'is_premium': True
            },
            {
                'email': 'sophie.tech@test.venturelink.com',
                'first_name': 'Sophie',
                'last_name': 'Leroy',
                'user_type': 'BOTH',
                'location': 'Toulouse, France'
            },
            {
                'email': 'pierre.startup@test.venturelink.com',
                'first_name': 'Pierre',
                'last_name': 'Bernard',
                'user_type': 'PROJECT_OWNER',
                'location': 'Marseille, France'
            },
            {
                'email': 'emma.fintech@test.venturelink.com',
                'first_name': 'Emma',
                'last_name': 'Moreau',
                'user_type': 'BOTH',
                'location': 'Bordeaux, France',
                'is_verified': True
            }
        ]
        
        for data in user_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'user_type': data['user_type'],
                    'location': data.get('location'),
                    'is_verified': data.get('is_verified', False),
                    'is_premium': data.get('is_premium', False),
                    'is_active': True,
                }
            )
            users.append(user)
            
        return users

    def create_categories(self):
        """Crée les catégories de projets"""
        categories_data = [
            {
                'name_fr': 'Technologie',
                'name_en': 'Technology',
                'icon': 'computer',
                'description_fr': 'Projets technologiques et numériques',
                'description_en': 'Technology and digital projects'
            },
            {
                'name_fr': 'Santé',
                'name_en': 'Health',
                'icon': 'medical',
                'description_fr': 'Solutions de santé et bien-être',
                'description_en': 'Health and wellness solutions'
            },
            {
                'name_fr': 'Finance',
                'name_en': 'Finance',
                'icon': 'finance',
                'description_fr': 'FinTech et services financiers',
                'description_en': 'FinTech and financial services'
            },
            {
                'name_fr': 'Environnement',
                'name_en': 'Environment',
                'icon': 'leaf',
                'description_fr': 'Solutions écologiques et durables',
                'description_en': 'Ecological and sustainable solutions'
            },
            {
                'name_fr': 'Éducation',
                'name_en': 'Education',
                'icon': 'book',
                'description_fr': 'EdTech et solutions éducatives',
                'description_en': 'EdTech and educational solutions'
            },
            {
                'name_fr': 'Commerce',
                'name_en': 'Commerce',
                'icon': 'shopping',
                'description_fr': 'E-commerce et retail',
                'description_en': 'E-commerce and retail'
            }
        ]
        
        categories = []
        for data in categories_data:
            category, created = ProjectCategory.objects.get_or_create(
                name_fr=data['name_fr'],
                defaults=data
            )
            categories.append(category)
            
        return categories

    def create_tags(self):
        """Crée les tags pour les projets"""
        tags_data = [
            {'name_fr': 'Intelligence Artificielle', 'name_en': 'Artificial Intelligence'},
            {'name_fr': 'Blockchain', 'name_en': 'Blockchain'},
            {'name_fr': 'Application Mobile', 'name_en': 'Mobile App'},
            {'name_fr': 'SaaS', 'name_en': 'SaaS'},
            {'name_fr': 'IoT', 'name_en': 'IoT'},
            {'name_fr': 'Machine Learning', 'name_en': 'Machine Learning'},
            {'name_fr': 'Startup', 'name_en': 'Startup'},
            {'name_fr': 'Innovation', 'name_en': 'Innovation'},
            {'name_fr': 'Durable', 'name_en': 'Sustainable'},
            {'name_fr': 'Social', 'name_en': 'Social'},
            {'name_fr': 'B2B', 'name_en': 'B2B'},
            {'name_fr': 'B2C', 'name_en': 'B2C'},
        ]
        
        tags = []
        for data in tags_data:
            tag, created = ProjectTag.objects.get_or_create(
                name_fr=data['name_fr'],
                defaults=data
            )
            tags.append(tag)
            
        return tags

    def create_projects_with_media(self, users, categories, tags, num_projects):
        """Crée des projets avec différents types de médias"""
        projects_data = [
            {
                'title': 'EcoTrack - Plateforme de suivi carbone',
                'short_description': 'Une application mobile qui permet aux entreprises de suivre et réduire leur empreinte carbone en temps réel.',
                'full_description': 'EcoTrack révolutionne la façon dont les entreprises gèrent leur impact environnemental. Notre plateforme combine IoT, IA et blockchain pour offrir un suivi précis des émissions de CO2. Les entreprises peuvent visualiser leurs données en temps réel, recevoir des recommandations personnalisées et participer à un marché de crédits carbone vérifié.',
                'category': 'Environnement',
                'stage': 'PROTOTYPE',
                'funding_min': 50000,
                'funding_max': 200000,
                'location_country': 'France',
                'location_city': 'Paris',
                'tags': ['Intelligence Artificielle', 'IoT', 'Blockchain', 'Durable'],
                'media_types': ['IMAGE', 'DOCUMENT']
            },
            {
                'title': 'MedConnect - Télémédecine nouvelle génération',
                'short_description': 'Plateforme de télémédecine avec IA pour diagnostic assisté et suivi patient personnalisé.',
                'full_description': 'MedConnect transforme l\'accès aux soins de santé grâce à une plateforme de télémédecine avancée. Utilisant l\'intelligence artificielle pour le pré-diagnostic, notre solution connecte patients et professionnels de santé. Nous proposons consultations vidéo HD, dossier médical numérique sécurisé, et monitoring à distance.',
                'category': 'Santé',
                'stage': 'DEVELOPMENT',
                'funding_min': 100000,
                'funding_max': 500000,
                'location_country': 'France',
                'location_city': 'Lyon',
                'tags': ['Intelligence Artificielle', 'Application Mobile', 'SaaS'],
                'media_types': ['IMAGE', 'DOCUMENT']
            },
            {
                'title': 'CryptoWallet Pro - Portefeuille multi-devises',
                'short_description': 'Portefeuille cryptocurrency sécurisé avec trading automatisé et gestion de portfolio avancée.',
                'full_description': 'CryptoWallet Pro est la solution complète pour gérer vos investissements cryptocurrency. Notre portefeuille multi-devises offre une sécurité de niveau bancaire avec authentification biométrique. Les fonctionnalités incluent le trading automatisé basé sur l\'IA et l\'analyse technique avancée.',
                'category': 'Finance',
                'stage': 'GROWTH',
                'funding_min': 200000,
                'funding_max': 1000000,
                'location_country': 'France',
                'location_city': 'Nice',
                'tags': ['Blockchain', 'Application Mobile', 'B2C'],
                'media_types': ['IMAGE']
            },
            {
                'title': 'EduAI - Assistant éducatif intelligent',
                'short_description': 'Plateforme d\'apprentissage personnalisée utilisant l\'IA pour adapter le contenu à chaque élève.',
                'full_description': 'EduAI révolutionne l\'éducation avec un assistant pédagogique alimenté par l\'intelligence artificielle. Notre plateforme analyse le style d\'apprentissage de chaque élève et adapte automatiquement le contenu. Nous proposons des cours interactifs, exercices gamifiés, et suivi temps réel des progrès.',
                'category': 'Éducation',
                'stage': 'PROTOTYPE',
                'funding_min': 75000,
                'funding_max': 300000,
                'location_country': 'France',
                'location_city': 'Toulouse',
                'tags': ['Intelligence Artificielle', 'SaaS', 'Innovation'],
                'media_types': ['IMAGE', 'DOCUMENT']
            },
            {
                'title': 'SmartFarm - Agriculture connectée',
                'short_description': 'Solution IoT pour optimiser les rendements agricoles avec capteurs intelligents et prédictions météo.',
                'full_description': 'SmartFarm apporte l\'agriculture 4.0 aux exploitants avec un écosystème IoT complet. Nos capteurs surveillent l\'humidité du sol, la température, les nutriments et la croissance des cultures. L\'IA analyse ces données pour optimiser l\'irrigation et prédire les rendements.',
                'category': 'Technologie',
                'stage': 'DEVELOPMENT',
                'funding_min': 150000,
                'funding_max': 600000,
                'location_country': 'France',
                'location_city': 'Bordeaux',
                'tags': ['IoT', 'Intelligence Artificielle', 'Durable', 'B2B'],
                'media_types': ['IMAGE', 'VIDEO', 'DOCUMENT']
            },
            {
                'title': 'FitCoach - Coach sportif virtuel',
                'short_description': 'Application de coaching sportif personnalisé avec IA et suivi biométrique en temps réel.',
                'full_description': 'FitCoach révolutionne le fitness avec un coach virtuel alimenté par l\'IA. Notre app analyse la forme physique, crée des programmes personnalisés et suit les progrès en temps réel. Intégration avec wearables et conseils nutritionnels inclus.',
                'category': 'Santé',
                'stage': 'IDEA',
                'funding_min': 80000,
                'funding_max': 350000,
                'location_country': 'France',
                'location_city': 'Montpellier',
                'tags': ['Intelligence Artificielle', 'Application Mobile', 'B2C', 'Innovation'],
                'media_types': ['IMAGE', 'VIDEO']
            }
        ]
        
        projects = []
        project_owners = [u for u in users if u.user_type in ['PROJECT_OWNER', 'BOTH']]
        
        # Limiter le nombre de projets selon le paramètre
        limited_projects = projects_data[:min(num_projects, len(projects_data))]
        
        for i, data in enumerate(limited_projects):
            # Sélectionner un créateur
            creator = project_owners[i % len(project_owners)]
            
            # Trouver la catégorie
            category = next((c for c in categories if c.name_fr == data['category']), categories[0])
            
            # Créer le projet
            project = Project.objects.create(
                creator=creator,
                title=data['title'],
                short_description=data['short_description'],
                full_description=data['full_description'],
                category=category,
                stage=data['stage'],
                funding_min=data['funding_min'],
                funding_max=data['funding_max'],
                funding_currency='EUR',
                location_country=data['location_country'],
                location_city=data['location_city'],
                is_draft=False,
                status='ACTIVE',
                published_at=timezone.now(),
                views_count=i * 47 + 12,
                interests_count=i * 8 + 3,
                favorites_count=i * 5 + 1,
            )
            
            # Ajouter les tags
            project_tags = [t for t in tags if t.name_fr in data['tags']]
            project.tags.set(project_tags)
            
            # Ajouter les médias
            self.create_media_for_project(project, data['media_types'])
            
            projects.append(project)
            
        return projects

    def create_media_for_project(self, project, media_types):
        """Crée différents types de médias pour un projet"""
        media_count = 0
        
        if 'IMAGE' in media_types:
            # Créer des images de test en utilisant des services gratuits
            project_hash = hash(str(project.id)) % 10000  # Convertir UUID en nombre
            image_urls = [
                f'https://picsum.photos/800/600?random={project_hash}',
                f'https://picsum.photos/800/600?random={project_hash + 100}',
            ]
            
            for i, url in enumerate(image_urls):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        filename = f'project_{project.id}_image_{i+1}.jpg'
                        content = ContentFile(response.content, filename)
                        
                        ProjectMedia.objects.create(
                            project=project,
                            file=content,
                            media_type='IMAGE',
                            title=f'Image {i+1} - {project.title}',
                            description=f'Image de présentation du projet {project.title}',
                            is_primary=(i == 0),
                            order=i
                        )
                        media_count += 1
                        self.stdout.write(f'   📸 Image {i+1} ajoutée pour {project.title}')
                except Exception as e:
                    self.stdout.write(f'   ⚠️ Erreur téléchargement image: {e}')
        
        if 'VIDEO' in media_types:
            # Créer des vidéos de test en utilisant des fichiers de test courts
            try:
                # Utiliser une vidéo de test courte (sample video)
                video_url = 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4'
                response = requests.get(video_url, timeout=60)
                if response.status_code == 200:
                    filename = f'project_{project.id}_video.mp4'
                    content = ContentFile(response.content, filename)
                    
                    ProjectMedia.objects.create(
                        project=project,
                        file=content,
                        media_type='VIDEO',
                        title=f'Vidéo de présentation - {project.title}',
                        description=f'Vidéo explicative du projet {project.title}',
                        order=media_count
                    )
                    media_count += 1
                    self.stdout.write(f'   🎥 Vidéo ajoutée pour {project.title}')
                else:
                    self.stdout.write(f'   ⚠️ Impossible de télécharger la vidéo (status: {response.status_code})')
            except Exception as e:
                self.stdout.write(f'   ⚠️ Erreur téléchargement vidéo: {e}')
        
        if 'DOCUMENT' in media_types:
            # Créer des documents de test
            documents = [
                {
                    'name': 'business_plan',
                    'title': 'Business Plan',
                    'content': self.generate_business_plan_content(project)
                },
                {
                    'name': 'presentation',
                    'title': 'Présentation Projet',
                    'content': self.generate_presentation_content(project)
                }
            ]
            
            for doc in documents:
                try:
                    filename = f'project_{project.id}_{doc["name"]}.txt'
                    content = ContentFile(doc['content'].encode('utf-8'), filename)
                    
                    ProjectMedia.objects.create(
                        project=project,
                        file=content,
                        media_type='DOCUMENT',
                        title=doc['title'],
                        description=f'{doc["title"]} du projet {project.title}',
                        order=media_count
                    )
                    media_count += 1
                    self.stdout.write(f'   📄 Document {doc["title"]} ajouté pour {project.title}')
                except Exception as e:
                    self.stdout.write(f'   ⚠️ Erreur création document: {e}')

    def generate_business_plan_content(self, project):
        """Génère le contenu d'un business plan de test"""
        return f"""BUSINESS PLAN - {project.title}

1. RÉSUMÉ EXÉCUTIF
{project.short_description}

2. DESCRIPTION DU PROJET
{project.full_description}

3. MARCHÉ CIBLE
Notre solution s'adresse aux entreprises cherchant à innover dans le secteur {project.category.name_fr}.
Le marché représente un potentiel de plusieurs milliards d'euros.

4. MODÈLE ÉCONOMIQUE
- Abonnement mensuel SaaS
- Commission sur les transactions
- Services de consulting

5. ÉQUIPE
Équipe expérimentée dirigée par {project.creator.get_full_name()}.

6. FINANCEMENT DEMANDÉ
Entre {project.funding_min}€ et {project.funding_max}€ pour le développement et la commercialisation.

7. RETOUR SUR INVESTISSEMENT
ROI estimé à 300% sur 5 ans.

8. PLAN DE DÉVELOPPEMENT
Phase 1: Prototype ({project.stage})
Phase 2: Version beta
Phase 3: Commercialisation
Phase 4: Expansion internationale
        """

    def generate_presentation_content(self, project):
        """Génère le contenu d'une présentation de test"""
        return f"""PRÉSENTATION PROJET - {project.title}

🚀 VISION
{project.short_description}

💡 PROBLÈME RÉSOLU
Les entreprises du secteur {project.category.name_fr} font face à de nombreux défis.
Notre solution apporte une réponse innovante et scalable.

🎯 SOLUTION
{project.full_description}

📊 MARCHÉ
- Taille du marché: X milliards €
- Croissance annuelle: X%
- Compétiteurs identifiés: X

👥 ÉQUIPE
Fondateur: {project.creator.get_full_name()}
Localisation: {project.location_city}, {project.location_country}

💰 FINANCEMENT
Recherche de {project.funding_min}€ à {project.funding_max}€

📈 PROJECTIONS
Année 1: Développement produit
Année 2: Premiers clients
Année 3: Expansion
Année 4-5: Rentabilité et croissance

🏆 AVANTAGES CONCURRENTIELS
- Innovation technologique
- Équipe expérimentée
- Timing optimal
- Partenariats stratégiques
        """ 