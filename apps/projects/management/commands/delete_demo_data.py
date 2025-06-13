from django.core.management.base import BaseCommand
from apps.users.models import User, Profile
from apps.projects.models import (
    Project, ProjectCategory, ProjectTag, ProjectNeeds, ProjectSkillsNeeded, ProjectMedia, ProjectFavorite, ProjectInterest
)
from django.db import transaction

class Command(BaseCommand):
    help = "Supprime les utilisateurs et projets factices générés pour les tests."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Suppression des données de test..."))

        # 1. Supprimer les interactions (favoris, intérêts)
        favs = ProjectFavorite.objects.filter(user__email__startswith="testuser")
        favs_count = favs.count()
        favs.delete()
        interests = ProjectInterest.objects.filter(user__email__startswith="testuser")
        interests_count = interests.count()
        interests.delete()

        # 2. Supprimer les médias, besoins, compétences liés aux projets de test
        projects = Project.objects.filter(title__icontains="Projet")
        medias = ProjectMedia.objects.filter(project__in=projects)
        needs = ProjectNeeds.objects.filter(project__in=projects)
        skills = ProjectSkillsNeeded.objects.filter(project__in=projects)
        medias_count = medias.count()
        needs_count = needs.count()
        skills_count = skills.count()
        medias.delete()
        needs.delete()
        skills.delete()

        # 3. Supprimer les projets de test
        projects_count = projects.count()
        projects.delete()

        # 4. Supprimer les utilisateurs de test
        users = User.objects.filter(email__startswith="testuser")
        users_count = users.count()
        for user in users:
            try:
                profile = Profile.objects.get(user=user)
                profile.delete()
            except Profile.DoesNotExist:
                pass
            user.delete()

        # 5. (Optionnel) Supprimer les tags et catégories de test s'ils ne sont plus utilisés
        tags = ProjectTag.objects.filter(name_fr__in=["Innovation", "Impact social", "Croissance", "Durabilité", "Jeunesse", "Femmes"])
        tags_count = tags.count()
        for tag in tags:
            if tag.projects.count() == 0:
                tag.delete()
        categories = ProjectCategory.objects.filter(name_fr__in=[
            "Agriculture", "Technologie financière", "Énergie", "Santé", "Éducation", "Transport", "Commerce", "Tourisme"
        ])
        categories_count = categories.count()
        for cat in categories:
            if cat.projects.count() == 0:
                cat.delete()

        self.stdout.write(self.style.SUCCESS(f"Suppression terminée : {users_count} utilisateurs, {projects_count} projets, {favs_count} favoris, {interests_count} intérêts, {medias_count} médias, {needs_count} besoins, {skills_count} compétences, {tags_count} tags, {categories_count} catégories (si non utilisées) supprimés.")) 