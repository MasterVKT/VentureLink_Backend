"""
Tests pour les modèles de l'application projects.
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.users.models import User
from apps.projects.models import (
    Project, ProjectCategory, ProjectTag, ProjectMedia,
    ProjectNeed, ProjectSkillNeeded, ProjectDocument
)


class ProjectCategoryModelTest(TestCase):
    """Tests pour le modèle ProjectCategory."""

    def setUp(self):
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology',
            description_fr='Projets technologiques',
            description_en='Technology projects',
            icon='technology'
        )

    def test_category_creation(self):
        """Test la création d'une catégorie de projet."""
        self.assertEqual(self.category.name_fr, 'Technologie')
        self.assertEqual(self.category.name_en, 'Technology')
        self.assertEqual(str(self.category), 'Technologie')
        self.assertTrue(self.category.is_active)


class ProjectTagModelTest(TestCase):
    """Tests pour le modèle ProjectTag."""

    def setUp(self):
        self.tag = ProjectTag.objects.create(
            name_fr='Intelligence Artificielle',
            name_en='Artificial Intelligence',
        )

    def test_tag_creation(self):
        """Test la création d'un tag de projet."""
        self.assertEqual(self.tag.name_fr, 'Intelligence Artificielle')
        self.assertEqual(self.tag.name_en, 'Artificial Intelligence')
        self.assertEqual(str(self.tag), 'Intelligence Artificielle')
        self.assertTrue(self.tag.is_active)


class ProjectModelTest(TestCase):
    """Tests pour le modèle Project."""

    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='test@venturelink.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Créer une catégorie
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        
        # Créer un projet
        self.project = Project.objects.create(
            creator=self.user,
            title='Projet de test très prometteur',
            short_description='Une description courte du projet de test pour les besoins des tests',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category,
            stage=Project.STAGE_PROTOTYPE,
            funding_min=Decimal('10000.00'),
            funding_max=Decimal('50000.00'),
            funding_currency='EUR',
            location_country='France',
            location_city='Paris'
        )
        
        # Créer des tags
        self.tag1 = ProjectTag.objects.create(name_fr='Tag 1', name_en='Tag 1')
        self.tag2 = ProjectTag.objects.create(name_fr='Tag 2', name_en='Tag 2')
        
        # Ajouter les tags au projet
        self.project.tags.add(self.tag1, self.tag2)

    def test_project_creation(self):
        """Test la création d'un projet."""
        self.assertEqual(self.project.creator, self.user)
        self.assertEqual(self.project.title, 'Projet de test très prometteur')
        self.assertEqual(self.project.category, self.category)
        self.assertEqual(self.project.stage, Project.STAGE_PROTOTYPE)
        self.assertEqual(self.project.funding_min, Decimal('10000.00'))
        self.assertEqual(self.project.funding_max, Decimal('50000.00'))
        self.assertEqual(self.project.funding_currency, 'EUR')
        self.assertEqual(self.project.tags.count(), 2)
        self.assertTrue(self.project.is_draft)
        self.assertFalse(self.project.is_premium)
        self.assertFalse(self.project.is_featured)
        self.assertEqual(self.project.status, Project.STATUS_ACTIVE)
        self.assertEqual(self.project.views_count, 0)
        self.assertEqual(self.project.interests_count, 0)
        self.assertEqual(self.project.favorites_count, 0)
        self.assertIsNone(self.project.published_at)

    def test_funding_validation(self):
        """Test que funding_max doit être supérieur à funding_min."""
        self.project.funding_min = Decimal('60000.00')
        self.project.funding_max = Decimal('50000.00')
        
        # La sauvegarde devrait lever une exception
        with self.assertRaises(ValidationError):
            self.project.save()


class ProjectMediaModelTest(TestCase):
    """Tests pour le modèle ProjectMedia."""

    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='test@venturelink.com',
            password='testpassword'
        )
        
        # Créer une catégorie
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        
        # Créer un projet
        self.project = Project.objects.create(
            creator=self.user,
            title='Projet de test très prometteur',
            short_description='Une description courte du projet de test pour les besoins des tests',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category
        )
        
        # Créer un média (simulé car nous ne pouvons pas manipuler de vrais fichiers dans les tests)
        self.media = ProjectMedia.objects.create(
            project=self.project,
            media_type=ProjectMedia.TYPE_IMAGE,
            title='Image test',
            is_primary=True,
            order=1
        )

    def test_media_creation(self):
        """Test la création d'un média de projet."""
        self.assertEqual(self.media.project, self.project)
        self.assertEqual(self.media.media_type, ProjectMedia.TYPE_IMAGE)
        self.assertEqual(self.media.title, 'Image test')
        self.assertTrue(self.media.is_primary)
        self.assertEqual(self.media.order, 1)
        self.assertEqual(str(self.media), 'Image test')


class ProjectNeedModelTest(TestCase):
    """Tests pour le modèle ProjectNeed."""

    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='test@venturelink.com',
            password='testpassword'
        )
        
        # Créer une catégorie
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        
        # Créer un projet
        self.project = Project.objects.create(
            creator=self.user,
            title='Projet de test très prometteur',
            short_description='Une description courte du projet de test pour les besoins des tests',
            full_description='Une description plus longue et détaillée du projet de test qui contient suffisamment de caractères pour passer la validation.',
            category=self.category
        )
        
        # Créer un besoin de projet
        self.need = ProjectNeed.objects.create(
            project=self.project,
            need_type=ProjectNeed.TYPE_FUNDING,
            title='Financement initial',
            description='Recherche de financement pour démarrer le projet',
            amount=Decimal('25000.00'),
            currency='EUR'
        )

    def test_need_creation(self):
        """Test la création d'un besoin de projet."""
        self.assertEqual(self.need.project, self.project)
        self.assertEqual(self.need.need_type, ProjectNeed.TYPE_FUNDING)
        self.assertEqual(self.need.title, 'Financement initial')
        self.assertEqual(self.need.amount, Decimal('25000.00'))
        self.assertEqual(self.need.currency, 'EUR')
        self.assertEqual(str(self.need), 'Financement initial') 