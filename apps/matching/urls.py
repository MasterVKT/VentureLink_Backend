"""
URLs for the matching app.
"""
from django.urls import path
from apps.matching.views.discover_views import DiscoverView

app_name = 'matching'

urlpatterns = [
    path('discover/', DiscoverView.as_view(), name='discover'),
]
