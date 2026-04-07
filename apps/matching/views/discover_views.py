"""
Views for the Discover API endpoint.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Q, Count
from django.utils import timezone
from datetime import timedelta
import logging

from apps.projects.models.project import Project
from apps.projects.serializers.project_serializer import ProjectListSerializer
from apps.matching.services import MatchingService

logger = logging.getLogger(__name__)


class DiscoverView(APIView):
    """
    API Discover retournant 4 sections de projets :
    - recommended : Basé sur matching IA
    - trending : Projets avec le plus d'activité récente
    - new : Projets récemment créés
    - almost_funded : Projets proches de l'objectif
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retourner les 4 sections de projets.
        """
        user = request.user

        # 1. Projets Recommandés (Matching IA)
        matching_service = MatchingService(user)
        recommended_data = matching_service.get_recommended_projects(limit=10)

        recommended_projects = [item['project'] for item in recommended_data]
        recommended_scores = {str(item['project'].id): item['match_score'] for item in recommended_data}

        # 2. Projets Tendances
        # Critère : Plus de favoris/intérêts dans les 7 derniers jours
        week_ago = timezone.now() - timedelta(days=7)

        trending_projects = Project.objects.filter(
            status=Project.STATUS_ACTIVE,
            is_draft=False
        ).annotate(
            recent_favorites=Count(
                'favorites',
                filter=Q(favorites__created_at__gte=week_ago)
            ),
            recent_interests=Count(
                'interests',
                filter=Q(interests__created_at__gte=week_ago)
            ),
            trend_score=F('recent_favorites') * 2 + F('recent_interests')
        ).order_by('-trend_score', '-created_at')[:10]

        # 3. Nouveaux Projets
        # Projets créés dans les 14 derniers jours
        two_weeks_ago = timezone.now() - timedelta(days=14)

        new_projects = Project.objects.filter(
            status=Project.STATUS_ACTIVE,
            is_draft=False,
            created_at__gte=two_weeks_ago
        ).order_by('-created_at')[:10]

        # 4. Projets Presque Financés
        # Critère : 75-95% de l'objectif atteint
        almost_funded_projects = Project.objects.filter(
            status=Project.STATUS_ACTIVE,
            is_draft=False,
            funding_max__gt=0
        ).annotate(
            progress=F('funding_min') / F('funding_max')
        ).filter(
            progress__gte=0.75,
            progress__lt=0.95
        ).order_by('-progress', '-created_at')[:10]

        # Sérialiser tous les projets
        serializer_context = {'request': request}

        response_data = {
            'recommended': {
                'projects': ProjectListSerializer(
                    recommended_projects,
                    many=True,
                    context=serializer_context
                ).data,
                'match_scores': recommended_scores
            },
            'trending': ProjectListSerializer(
                trending_projects,
                many=True,
                context=serializer_context
            ).data,
            'new': ProjectListSerializer(
                new_projects,
                many=True,
                context=serializer_context
            ).data,
            'almost_funded': ProjectListSerializer(
                almost_funded_projects,
                many=True,
                context=serializer_context
            ).data,
        }

        logger.info(f"Discover API called for user {user.id}, returned {len(recommended_projects)} recommended projects")

        return Response(response_data)
