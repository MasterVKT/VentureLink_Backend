"""
URL patterns for project API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from apps.projects.views import (
    ProjectViewSet, ProjectCategoryViewSet, ProjectTagViewSet,
    ProjectMediaViewSet, ProjectNeedsViewSet, ProjectSkillsNeededViewSet,
    ProjectInterestViewSet, ProjectFavoriteViewSet,
    ProjectQuestionViewSet, ProjectQuestionAnswerViewSet
)
from apps.projects.views.project_interaction_views import ProjectReportViewSet
from apps.projects.views.project_views import ProjectSearchView, TrendingProjectsView


# Router principal pour les endpoints non-imbriqués
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', ProjectCategoryViewSet, basename='project-category')
router.register(r'tags', ProjectTagViewSet, basename='project-tag')
router.register(r'interests', ProjectInterestViewSet, basename='project-interest')
router.register(r'favorites', ProjectFavoriteViewSet, basename='project-favorite')
router.register(r'questions', ProjectQuestionViewSet, basename='project-question')
router.register(r'reports', ProjectReportViewSet, basename='project-report')

# Routers imbriqués pour les endpoints liés à un projet
projects_router = NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'media', ProjectMediaViewSet, basename='project-media')
projects_router.register(r'needs', ProjectNeedsViewSet, basename='project-needs')
projects_router.register(r'skills', ProjectSkillsNeededViewSet, basename='project-skills')
projects_router.register(r'reports', ProjectReportViewSet, basename='project-reports')

# Router imbriqué pour les réponses aux questions
questions_router = NestedDefaultRouter(router, r'questions', lookup='question')
questions_router.register(r'answers', ProjectQuestionAnswerViewSet, basename='question-answer')

# Compiler toutes les URLs
urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(questions_router.urls)),
    # Nouvelles routes pour recherche avancée
    path('search/', ProjectSearchView.as_view({'get': 'list'}), name='project-search'),
    path('trending/', TrendingProjectsView.as_view({'get': 'list'}), name='trending-projects'),
    path('categories-list/', ProjectCategoryViewSet.as_view({'get': 'list'}), name='categories-list'),
] 