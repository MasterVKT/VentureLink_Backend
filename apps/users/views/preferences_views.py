from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

from apps.users.models.user_preferences import UserPreferences
from apps.users.serializers.user_preferences_serializer import UserPreferencesSerializer


class UserPreferencesViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les préférences utilisateur.
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Récupérer les préférences de l'utilisateur actuel.
        
        Returns:
            Response: Les préférences de l'utilisateur
        """
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """
        Mettre à jour les préférences de l'utilisateur actuel.
        
        Request body:
            - preferred_categories: Liste des catégories préférées
            - min_investment_amount: Montant minimum d'investissement
            - max_investment_amount: Montant maximum d'investissement
            - preferred_locations: Liste des localisations préférées
            - risk_tolerance: Tolérance au risque (low, medium, high)
        
        Returns:
            Response: Les préférences mises à jour
        """
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)
