from rest_framework import serializers
from apps.users.models.user_preferences import UserPreferences


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les préférences utilisateur.
    """
    class Meta:
        model = UserPreferences
        fields = [
            'preferred_categories',
            'min_investment_amount',
            'max_investment_amount',
            'preferred_locations',
            'risk_tolerance',
            'viewed_projects',
            'favorited_projects_count',
            'invested_projects_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'user',
            'viewed_projects',
            'favorited_projects_count',
            'invested_projects_count',
            'created_at',
            'updated_at',
        ]
