"""
Tests pour les vues de l'application projects.
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.projects.models import (
    Project, ProjectCategory, ProjectTag, ProjectMedia
)


class ProjectAPITest(TestCase):
    """Tests pour les API de projets."""

    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='test@venturelink.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Créer un autre utilisateur
        self.other_user = User.objects.create_user(
            email='other@venturelink.com',
            password='otherpassword',
            first_name='Other',
            last_name='User'
        )
        
        # Créer un administrateur
        self.admin_user = User.objects.create_user(
            email='admin@venturelink.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )
        
        # Créer des catégories
        self.category1 = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        self.category2 = ProjectCategory.objects.create(
            name_fr='Santé',
            name_en='Health'
        )
        
        # Créer des tags
        self.tag1 = ProjectTag.objects.create(name_fr='Web', name_en='Web')
        self.tag2 = ProjectTag.objects.create(name_fr='Mobile', name_en='Mobile')
        
        # Créer un projet
        self.project = Project.objects.create(
            creator=self.user,
            title='Projet de test très prometteur',
            short_description='Une description courte du projet de test pour les besoins des tests',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category1,
            stage=Project.STAGE_PROTOTYPE,
            funding_min=Decimal('10000.00'),
            funding_max=Decimal('50000.00'),
            funding_currency='EUR',
            location_country='France',
            location_city='Paris',
            is_draft=False  # Projet publié
        )
        
        # Ajouter des tags au projet
        self.project.tags.add(self.tag1, self.tag2)
        
        # Créer un projet en brouillon
        self.draft_project = Project.objects.create(
            creator=self.user,
            title='Projet brouillon',
            short_description='Une description courte du projet brouillon',
            full_description='Une description plus longue et détaillée du projet brouillon qui contient suffisamment de caractères pour passer la validation.',
            category=self.category2,
            is_draft=True
        )
        
        # Créer un projet d'un autre utilisateur
        self.other_project = Project.objects.create(
            creator=self.other_user,
            title='Projet d\'un autre utilisateur',
            short_description='Une description courte du projet d\'un autre utilisateur',
            full_description='Une description plus longue et détaillée du projet d\'un autre utilisateur qui contient suffisamment de caractères pour passer la validation.',
            category=self.category1,
            is_draft=False  # Projet publié
        )
        
        # Initialiser le client API
        self.client = APIClient()

    def test_list_projects_anonymous(self):
        """Test: un utilisateur anonyme peut voir les projets publiés."""
        url = reverse('project-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 2 projets publiés
        
        # Vérifier que les brouillons ne sont pas inclus
        project_ids = [project['id'] for project in response.data['results']]
        self.assertIn(str(self.project.id), project_ids)
        self.assertIn(str(self.other_project.id), project_ids)
        self.assertNotIn(str(self.draft_project.id), project_ids)

    def test_list_projects_authenticated(self):
        """Test: un utilisateur authentifié peut voir ses brouillons et les projets publiés."""
        self.client.force_authenticate(user=self.user)
        url = reverse('project-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Devrait voir tous les projets publiés + ses brouillons
        self.assertEqual(len(response.data['results']), 3)
        
        project_ids = [project['id'] for project in response.data['results']]
        self.assertIn(str(self.project.id), project_ids)
        self.assertIn(str(self.other_project.id), project_ids)
        self.assertIn(str(self.draft_project.id), project_ids)

    def test_retrieve_project_published(self):
        """Test: tout le monde peut consulter un projet publié."""
        url = reverse('project-detail', kwargs={'pk': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.project.id))
        self.assertEqual(response.data['title'], self.project.title)

    def test_retrieve_project_draft(self):
        """Test: les brouillons ne sont visibles que par leur créateur."""
        # Utilisateur anonyme
        url = reverse('project-detail', kwargs={'pk': self.draft_project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Autre utilisateur
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Créateur du projet
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.draft_project.id))

    def test_create_project(self):
        """Test: un utilisateur authentifié peut créer un projet."""
        self.client.force_authenticate(user=self.user)
        url = reverse('project-list')
        
        data = {
            'title': 'Nouveau projet de test',
            'short_description': 'Description courte du nouveau projet',
            'full_description': 'Description complète du nouveau projet qui doit être suffisamment longue pour passer la validation',
            'category': self.category1.id,
            'stage': Project.STAGE_IDEA,
            'funding_min': '5000.00',
            'funding_max': '20000.00',
            'funding_currency': 'EUR',
            'tags': [self.tag1.id]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que le projet a été créé
        self.assertTrue(Project.objects.filter(title='Nouveau projet de test').exists())
        new_project = Project.objects.get(title='Nouveau projet de test')
        self.assertEqual(new_project.creator, self.user)
        self.assertEqual(new_project.category, self.category1)
        self.assertTrue(new_project.is_draft)  # Par défaut, c'est un brouillon

    def test_update_project(self):
        """Test: un utilisateur peut modifier son propre projet."""
        self.client.force_authenticate(user=self.user)
        url = reverse('project-detail', kwargs={'pk': self.project.id})
        
        data = {
            'title': 'Projet modifié',
            'short_description': self.project.short_description,
            'funding_min': '15000.00'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier les modifications
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Projet modifié')
        self.assertEqual(self.project.funding_min, Decimal('15000.00'))

    def test_update_other_user_project(self):
        """Test: un utilisateur ne peut pas modifier le projet d'un autre utilisateur."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('project-detail', kwargs={'pk': self.project.id})
        
        data = {
            'title': 'Projet piraté',
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Vérifier que le projet n'a pas été modifié
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.title, 'Projet piraté')

    def test_publish_project(self):
        """Test: un utilisateur peut publier son projet brouillon."""
        self.client.force_authenticate(user=self.user)
        url = reverse('project-publish', kwargs={'pk': self.draft_project.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le projet est publié
        self.draft_project.refresh_from_db()
        self.assertFalse(self.draft_project.is_draft)
        self.assertIsNotNone(self.draft_project.published_at)

    def test_delete_project(self):
        """Test: un utilisateur peut supprimer son propre projet."""
        self.client.force_authenticate(user=self.user)
        url = reverse('project-detail', kwargs={'pk': self.project.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que le projet a été supprimé
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())

    def test_delete_other_user_project(self):
        """Test: un utilisateur ne peut pas supprimer le projet d'un autre utilisateur."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('project-detail', kwargs={'pk': self.project.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Vérifier que le projet n'a pas été supprimé
        self.assertTrue(Project.objects.filter(id=self.project.id).exists()) 