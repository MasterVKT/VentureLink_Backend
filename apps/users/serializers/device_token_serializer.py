"""
Sérialiseurs pour les tokens d'appareil.
"""
from rest_framework import serializers

from apps.users.models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les tokens d'appareil.
    """
    class Meta:
        model = DeviceToken
        fields = [
            'id', 'token', 'platform', 'device_id', 'device_name', 
            'app_version', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceTokenCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'un token d'appareil.
    """
    class Meta:
        model = DeviceToken
        fields = [
            'token', 'platform', 'device_id', 'device_name', 'app_version'
        ]
        
    def validate_platform(self, value):
        """
        Valide que la plateforme est dans la liste des choix.
        """
        valid_platforms = [choice[0] for choice in DeviceToken.PLATFORM_CHOICES]
        if value not in valid_platforms:
            raise serializers.ValidationError(
                f"Plateforme invalide. Valeurs autorisées: {', '.join(valid_platforms)}"
            )
        return value 