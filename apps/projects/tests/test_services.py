"""
Tests pour les services de l'application projects.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.users.models import User
from apps.projects.models import (
    Project, ProjectCategory, ProjectTag, ProjectNeed,
    ProjectMedia, ProjectInterest, ProjectFavorite
)
from apps.projects.services.project_service import ProjectService
from apps.projects.services.project_media_service import ProjectMediaService
from apps.projects.services.project_needs_service import ProjectNeedsService
from apps.projects.services.project_interaction_service import ProjectInteractionService
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError


class ProjectServiceTest(TestCase):
    """Tests pour le service ProjectService."""

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
            title='Projet de test',
            short_description='Une description courte du projet de test',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category1,
            stage=Project.STAGE_PROTOTYPE,
            funding_min=Decimal('10000.00'),
            funding_max=Decimal('50000.00'),
            funding_currency='EUR',
            is_draft=False  # Projet publié
        )
        
        # Ajouter des tags au projet
        self.project.tags.add(self.tag1, self.tag2)
        
        # Créer un projet en brouillon
        self.draft_project = Project.objects.create(
            creator=self.user,
            title='Projet brouillon',
            short_description='Une description courte du projet brouillon',
            full_description='Une description plus longue et détaillée du projet brouillon.',
            category=self.category2,
            is_draft=True
        )

    def test_get_projects(self):
        """Test la récupération des projets."""
        # Anonyme: ne voit que les projets publiés
        projects = ProjectService.get_projects(user=None)
        self.assertEqual(projects.count(), 1)
        self.assertIn(self.project, projects)
        self.assertNotIn(self.draft_project, projects)
        
        # Utilisateur authentifié: voit ses brouillons + projets publiés
        projects = ProjectService.get_projects(user=self.user)
        self.assertEqual(projects.count(), 2)
        self.assertIn(self.project, projects)
        self.assertIn(self.draft_project, projects)
        
        # Autre utilisateur: ne voit que les projets publiés
        projects = ProjectService.get_projects(user=self.other_user)
        self.assertEqual(projects.count(), 1)
        self.assertIn(self.project, projects)
        self.assertNotIn(self.draft_project, projects)

    def test_get_projects_with_filters(self):
        """Test la récupération des projets avec filtres."""
        # Filtrer par catégorie
        projects = ProjectService.get_projects(
            user=None,
            filters={'category': self.category1.id}
        )
        self.assertEqual(projects.count(), 1)
        self.assertIn(self.project, projects)
        
        # Filtrer par stage
        projects = ProjectService.get_projects(
            user=None,
            filters={'stage': Project.STAGE_PROTOTYPE}
        )
        self.assertEqual(projects.count(), 1)
        self.assertIn(self.project, projects)
        
        # Filtrer par catégorie qui ne correspond pas
        projects = ProjectService.get_projects(
            user=None,
            filters={'category': self.category2.id}
        )
        self.assertEqual(projects.count(), 0)

    def test_get_project_by_id(self):
        """Test la récupération d'un projet par ID."""
        # Projet publié: accessible à tous
        project = ProjectService.get_project_by_id(
            project_id=self.project.id,
            user=None
        )
        self.assertEqual(project, self.project)
        
        # Projet brouillon: accessible uniquement au créateur
        with self.assertRaises(ResourceNotFoundError):
            ProjectService.get_project_by_id(
                project_id=self.draft_project.id,
                user=None
            )
        
        with self.assertRaises(ResourceNotFoundError):
            ProjectService.get_project_by_id(
                project_id=self.draft_project.id,
                user=self.other_user
            )
        
        # Le créateur peut accéder à son brouillon
        project = ProjectService.get_project_by_id(
            project_id=self.draft_project.id,
            user=self.user
        )
        self.assertEqual(project, self.draft_project)

    def test_create_project(self):
        """Test la création d'un projet."""
        project_data = {
            'title': 'Nouveau projet',
            'short_description': 'Description courte du nouveau projet',
            'full_description': 'Description complète du nouveau projet qui doit être suffisamment longue.',
            'category': self.category1,
            'stage': Project.STAGE_IDEA,
            'funding_min': Decimal('5000.00'),
            'funding_max': Decimal('20000.00'),
            'funding_currency': 'EUR',
            'tags': [self.tag1, self.tag2]
        }
        
        project = ProjectService.create_project(
            user=self.user,
            data=project_data
        )
        
        self.assertEqual(project.creator, self.user)
        self.assertEqual(project.title, 'Nouveau projet')
        self.assertEqual(project.category, self.category1)
        self.assertEqual(project.stage, Project.STAGE_IDEA)
        self.assertEqual(project.funding_min, Decimal('5000.00'))
        self.assertEqual(project.funding_max, Decimal('20000.00'))
        self.assertEqual(project.funding_currency, 'EUR')
        self.assertEqual(project.tags.count(), 2)
        self.assertTrue(project.is_draft)  # Par défaut, c'est un brouillon

    def test_update_project(self):
        """Test la mise à jour d'un projet."""
        update_data = {
            'title': 'Projet mis à jour',
            'funding_min': Decimal('15000.00')
        }
        
        updated_project = ProjectService.update_project(
            project_id=self.project.id,
            user=self.user,
            data=update_data
        )
        
        self.assertEqual(updated_project.title, 'Projet mis à jour')
        self.assertEqual(updated_project.funding_min, Decimal('15000.00'))
        
        # Vérifier que les autres champs n'ont pas changé
        self.assertEqual(updated_project.short_description, self.project.short_description)
        self.assertEqual(updated_project.category, self.project.category)

    def test_update_project_other_user(self):
        """Test qu'un utilisateur ne peut pas mettre à jour le projet d'un autre."""
        update_data = {
            'title': 'Projet piraté',
        }
        
        with self.assertRaises(PermissionDeniedError):
            ProjectService.update_project(
                project_id=self.project.id,
                user=self.other_user,
                data=update_data
            )
        
        # Vérifier que le projet n'a pas été modifié
        self.project.refresh_from_db()
        self.assertNotEqual(self.project.title, 'Projet piraté')

    def test_delete_project(self):
        """Test la suppression d'un projet."""
        # Un utilisateur peut supprimer son propre projet
        ProjectService.delete_project(
            project_id=self.project.id,
            user=self.user
        )
        
        # Vérifier que le projet a été supprimé
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())

    def test_delete_project_other_user(self):
        """Test qu'un utilisateur ne peut pas supprimer le projet d'un autre."""
        with self.assertRaises(PermissionDeniedError):
            ProjectService.delete_project(
                project_id=self.project.id,
                user=self.other_user
            )
        
        # Vérifier que le projet n'a pas été supprimé
        self.assertTrue(Project.objects.filter(id=self.project.id).exists())

    def test_publish_project(self):
        """Test la publication d'un projet."""
        published_project = ProjectService.publish_project(
            project_id=self.draft_project.id,
            user=self.user
        )
        
        self.assertFalse(published_project.is_draft)
        self.assertIsNotNone(published_project.published_at)
        
        # Vérifier que la date de publication est proche de maintenant
        now = timezone.now()
        self.assertLess((now - published_project.published_at).total_seconds(), 10)

    def test_increment_view_count(self):
        """Test l'incrémentation du compteur de vues."""
        initial_views = self.project.views_count
        
        ProjectService.increment_view_count(self.project.id)
        
        # Vérifier que le compteur a été incrémenté
        self.project.refresh_from_db()
        self.assertEqual(self.project.views_count, initial_views + 1) 