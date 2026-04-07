from django.db.models import Q, Count, F
from apps.projects.models.project import Project
from apps.users.models.user_preferences import UserPreferences
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service de matching IA pour recommander des projets aux utilisateurs.
    """

    def __init__(self, user):
        self.user = user
        self.preferences = self._get_or_create_preferences()

    def _get_or_create_preferences(self) -> UserPreferences:
        """Récupérer ou créer les préférences utilisateur"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.user
        )
        if created:
            logger.info(f"Created new preferences for user {self.user.id}")
        return preferences

    def calculate_match_score(self, project: Project) -> float:
        """
        Calculer un score de matching entre 0.0 et 1.0.

        Critères :
        - Catégorie préférée : 30%
        - Budget compatible : 25%
        - Localisation préférée : 20%
        - Popularité (vues, favoris) : 15%
        - Risque toléré : 10%
        """
        score = 0.0

        # 1. Score catégorie (0.0 - 0.3)
        if self.preferences.preferred_categories:
            if project.category.slug in self.preferences.preferred_categories:
                score += 0.3
            # Bonus partiel si catégorie similaire
            elif any(cat.lower() in project.category.name_fr.lower()
                    for cat in self.preferences.preferred_categories):
                score += 0.15
        else:
            # Si pas de préférence, score neutre
            score += 0.15

        # 2. Score budget (0.0 - 0.25)
        if self.preferences.min_investment_amount > 0:
            min_inv = float(self.preferences.min_investment_amount)
            max_inv = float(self.preferences.max_investment_amount) if self.preferences.max_investment_amount else float('inf')

            # Use funding_min as the project's minimum funding goal
            project_goal = float(project.funding_min) if project.funding_min else float(project.funding_max) if project.funding_max else 0

            if project_goal > 0:
                if min_inv <= project_goal <= max_inv:
                    score += 0.25
                elif project_goal < min_inv:
                    # Pénalité si trop petit
                    score += max(0, 0.25 * (project_goal / min_inv))
                else:
                    # Pénalité si trop grand
                    score += max(0, 0.25 * (max_inv / project_goal))
            else:
                score += 0.15
        else:
            score += 0.15

        # 3. Score localisation (0.0 - 0.2)
        if self.preferences.preferred_locations:
            project_location = ""
            if project.location_city:
                project_location += project.location_city.lower()
            if project.location_country:
                project_location += " " + project.location_country.lower()
            
            if any(loc.lower() in project_location for loc in self.preferences.preferred_locations):
                score += 0.2
        else:
            score += 0.1

        # 4. Score popularité (0.0 - 0.15)
        # Basé sur nombre de favoris et vues
        favorites_count = getattr(project, 'favorites_count', 0)
        views_count = getattr(project, 'views_count', 0)

        popularity_score = min(
            0.15,
            (favorites_count * 0.02) + (views_count * 0.0001)
        )
        score += popularity_score

        # 5. Score risque (0.0 - 0.1)
        # Using project stage as a proxy for risk
        # IDEA is riskiest, GROWTH is safest
        stage_risk_map = {
            Project.STAGE_IDEA: 0.0,
            Project.STAGE_PROTOTYPE: 0.33,
            Project.STAGE_DEVELOPMENT: 0.66,
            Project.STAGE_GROWTH: 1.0,
        }
        progress = stage_risk_map.get(project.stage, 0.5)

        if self.preferences.risk_tolerance == 'low':
            # Préfère projets déjà bien avancés (moins risqués)
            score += progress * 0.1
        elif self.preferences.risk_tolerance == 'high':
            # Préfère projets nouveaux (plus de potentiel, plus risqués)
            score += (1 - progress) * 0.1
        else:
            # Neutre
            score += 0.05

        return round(score, 3)

    def get_recommended_projects(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retourner les projets recommandés pour l'utilisateur.
        """
        # Exclure projets déjà vus
        viewed_ids = [str(pid) for pid in self.preferences.viewed_projects]
        exclude_ids = set(viewed_ids)

        # Exclude projects where user is the creator
        exclude_ids.add(str(self.user.id))

        # Récupérer tous les projets publiés
        projects = Project.objects.filter(
            status=Project.STATUS_ACTIVE,
            is_draft=False
        ).exclude(
            creator=self.user
        ).select_related(
            'creator',
            'category'
        ).prefetch_related(
            'tags',
            'media'
        )

        # Calculer les scores
        projects_with_scores = []
        for project in projects:
            score = self.calculate_match_score(project)
            projects_with_scores.append((project, score))

        # Trier par score décroissant
        projects_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Retourner top N avec leurs scores
        top_projects = [
            {
                'project': p,
                'match_score': score
            }
            for p, score in projects_with_scores[:limit]
        ]

        logger.info(f"Generated {len(top_projects)} recommendations for user {self.user.id}")

        return top_projects

    def record_interaction(self, project: Project, interaction_type: str):
        """
        Enregistrer une interaction pour améliorer les recommandations.

        Types : 'view', 'favorite', 'interest', 'invest'
        """
        if interaction_type == 'view':
            project_id_str = str(project.id)
            if project_id_str not in self.preferences.viewed_projects:
                viewed = self.preferences.viewed_projects
                viewed.append(project_id_str)
                self.preferences.viewed_projects = viewed
                self.preferences.save(update_fields=['_viewed_projects', 'updated_at'])

        elif interaction_type == 'favorite':
            self.preferences.favorited_projects_count += 1
            self.preferences.save(update_fields=['favorited_projects_count', 'updated_at'])

        elif interaction_type == 'interest':
            self.preferences.save(update_fields=['updated_at'])

        elif interaction_type == 'invest':
            self.preferences.invested_projects_count += 1
            self.preferences.save(update_fields=['invested_projects_count', 'updated_at'])
