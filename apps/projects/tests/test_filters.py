"""
Tests pour les filtres avancés de projets.
"""
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory, ProjectTag


class ProjectFiltersTests(APITestCase):
    """
    Tests pour les filtres avancés sur les projets.
    """
    
    def setUp(self):
        """
        Configuration avant chaque test.
        """
        # Créer des utilisateurs
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='securepassword123',
            first_name='Jean',
            last_name='Dupont'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='securepassword123',
            first_name='Marie',
            last_name='Martin'
        )
        
        # Créer des catégories
        self.category1 = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology',
            description_fr='Projets technologiques',
            description_en='Technology projects'
        )
        
        self.category2 = ProjectCategory.objects.create(
            name_fr='Finance',
            name_en='Finance',
            description_fr='Projets financiers',
            description_en='Financial projects'
        )
        
        # Créer des tags
        self.tag1 = ProjectTag.objects.create(name_fr='AI', name_en='AI')
        self.tag2 = ProjectTag.objects.create(name_fr='Blockchain', name_en='Blockchain')
        self.tag3 = ProjectTag.objects.create(name_fr='Mobile', name_en='Mobile')
        
        # Créer des projets publiés
        self.project1 = Project.objects.create(
            creator=self.user1,
            title='Projet IA Innovant',
            short_description='Une plateforme IA pour l\'analyse des données',
            full_description='Description détaillée du projet IA',
            category=self.category1,
            stage=Project.STAGE_PROTOTYPE,
            funding_min=Decimal('50000.00'),
            funding_max=Decimal('100000.00'),
            funding_currency='EUR',
            location_country='France',
            location_city='Paris',
            is_draft=False,
            published_at=timezone.now()
        )
        self.project1.tags.add(self.tag1)
        
        self.project2 = Project.objects.create(
            creator=self.user2,
            title='Application Mobile de Finance',
            short_description='Gérez vos finances facilement',
            full_description='Application de gestion financière',
            category=self.category2,
            stage=Project.STAGE_DEVELOPMENT,
            funding_min=Decimal('20000.00'),
            funding_max=Decimal('40000.00'),
            funding_currency='USD',
            location_country='USA',
            location_city='New York',
            is_draft=False,
            published_at=timezone.now()
        )
        self.project2.tags.add(self.tag2, self.tag3)
        
        # Projet non publié
        self.project3 = Project.objects.create(
            creator=self.user1,
            title='Projet Secret',
            short_description='À venir',
            full_description='Projet en cours de développement',
            category=self.category1,
            is_draft=True
        )
        
        # URL pour les tests
        self.projects_url = reverse('project-list')
        self.filter_options_url = reverse('project-filter-options')
        
    def test_filter_by_category(self):
        """
        Test du filtrage par catégorie.
        """
        response = self.client.get(f"{self.projects_url}?category={self.category1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que seuls les projets de la catégorie 1 sont retournés
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
    
    def test_filter_by_tags(self):
        """
        Test du filtrage par tags.
        """
        response = self.client.get(f"{self.projects_url}?tags={self.tag1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
        
        # Filtrer par plusieurs tags
        response = self.client.get(f"{self.projects_url}?tags={self.tag2.id},{self.tag3.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project2.id))
    
    def test_filter_by_location(self):
        """
        Test du filtrage par localisation.
        """
        response = self.client.get(f"{self.projects_url}?location_country=France")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
        
        response = self.client.get(f"{self.projects_url}?location_city=York")  # Recherche partielle
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project2.id))
    
    def test_filter_by_funding(self):
        """
        Test du filtrage par montants de financement.
        """
        response = self.client.get(f"{self.projects_url}?funding_min=30000")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
        
        # Test avec conversion de devise (l'USD sera converti en EUR)
        response = self.client.get(f"{self.projects_url}?funding_max=50000&funding_currency=EUR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: ce test dépend des taux de change qui sont mockés ou réels selon l'environnement
    
    def test_filter_by_stage(self):
        """
        Test du filtrage par stade de développement.
        """
        response = self.client.get(f"{self.projects_url}?stage={Project.STAGE_PROTOTYPE}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
        
        # Test avec plusieurs stades
        response = self.client.get(
            f"{self.projects_url}?stage={Project.STAGE_PROTOTYPE},{Project.STAGE_DEVELOPMENT}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_search(self):
        """
        Test de la recherche textuelle.
        """
        response = self.client.get(f"{self.projects_url}?search=IA")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project1.id))
        
        # Recherche dans le nom du créateur
        response = self.client.get(f"{self.projects_url}?search=Marie")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.project2.id))
    
    def test_filter_options(self):
        """
        Test de récupération des options de filtrage.
        """
        response = self.client.get(self.filter_options_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que toutes les sections sont présentes
        self.assertIn('stage_choices', response.data)
        self.assertIn('status_choices', response.data)
        self.assertIn('countries', response.data)
        self.assertIn('categories', response.data)
        self.assertIn('tags', response.data)
        
        # Vérifier le contenu des sections
        self.assertEqual(len(response.data['countries']), 2)
        self.assertEqual(len(response.data['categories']), 2)
        self.assertEqual(len(response.data['tags']), 3)
    
    def test_draft_projects_visibility(self):
        """
        Test de la visibilité des projets en brouillon.
        """
        # Anonyme ne voit pas les brouillons
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Seulement les projets publiés
        
        # Le créateur voit ses propres brouillons
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # Tous les projets, y compris son brouillon
        
        # Un autre utilisateur ne voit pas les brouillons des autres
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.projects_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Seulement les projets publiés
    
    def test_trending_projects(self):
        """
        Test de récupération des projets tendance.
        """
        # Simuler des vues et intérêts sur le projet 1
        self.project1.views_count = 100
        self.project1.interests_count = 50
        self.project1.save()
        
        # Simuler des vues et intérêts sur le projet 2 (moins nombreux)
        self.project2.views_count = 30
        self.project2.interests_count = 10
        self.project2.save()
        
        response = self.client.get(reverse('project-trending'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Le projet 1 devrait être en premier (plus de vues et intérêts)
        self.assertEqual(response.data[0]['id'], str(self.project1.id))
    
    def test_related_projects(self):
        """
        Test de récupération des projets liés.
        """
        # Créer un autre projet dans la même catégorie que le projet 1
        project4 = Project.objects.create(
            creator=self.user2,
            title='Autre Projet Tech',
            short_description='Un autre projet tech',
            full_description='Description du projet tech',
            category=self.category1,
            is_draft=False,
            published_at=timezone.now()
        )
        
        # Obtenir les projets liés au projet 1
        response = self.client.get(reverse('project-related', args=[self.project1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(project4.id))
        
        # Les brouillons ne devraient pas apparaître dans les projets liés
        project5 = Project.objects.create(
            creator=self.user1,
            title='Projet Tech en Brouillon',
            short_description='Un brouillon',
            full_description='Description',
            category=self.category1,
            is_draft=True
        )
        
        response = self.client.get(reverse('project-related', args=[self.project1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Toujours un seul projet 