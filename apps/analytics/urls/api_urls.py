"""
URLs API pour les métriques et statistiques.
"""
from django.urls import path

from apps.analytics.views import (
    UserMetricsView, ProjectMetricsView,
    DashboardMetricsView, TopProjectsView
)

app_name = 'analytics'

urlpatterns = [
    # Métriques utilisateur
    path('user/', UserMetricsView, name='user-metrics'),
    
    # Métriques projet
    path('project/<uuid:project_id>/', ProjectMetricsView, name='project-metrics'),
    
    # Métriques tableau de bord
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    
    # Projets les plus performants
    path('top-projects/', TopProjectsView.as_view(), name='top-projects'),
] 