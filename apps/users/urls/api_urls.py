"""
URLs pour les APIs de l'application users.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import (
    UserViewSet, ProfileViewSet, SubscriptionViewSet, DeviceTokenViewSet
)
from apps.users.views.company_profile_views import (
    CompanyProfileViewSet, MyCompanyProfileView, CompanyListView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'device-tokens', DeviceTokenViewSet, basename='device-token')
router.register(r'companies', CompanyProfileViewSet, basename='company')

urlpatterns = [
    path('', include(router.urls)),
    path('my-company/', MyCompanyProfileView.as_view(), name='my-company'),
    path('companies/list/', CompanyListView.as_view(), name='company-list'),
] 