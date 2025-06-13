"""
Vues pour la gestion des tokens d'appareil.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import DeviceToken
from apps.users.serializers.device_token_serializer import (
    DeviceTokenSerializer, DeviceTokenCreateSerializer
)
from apps.users.services import DeviceTokenService
from apps.core.permissions import IsOwner
from apps.core.exceptions import ResourceNotFoundError, ValidationError


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les tokens d'appareil.
    
    Endpoints:
    - GET /api/v1/device-tokens/: Liste tous les tokens de l'utilisateur courant
    - POST /api/v1/device-tokens/: Enregistre un nouveau token
    - GET /api/v1/device-tokens/{id}/: Récupère les détails d'un token
    - DELETE /api/v1/device-tokens/{id}/: Désactive un token
    - POST /api/v1/device-tokens/deactivate-by-device/: Désactive tous les tokens d'un appareil
    """
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        """Retourne les tokens de l'utilisateur courant."""
        return DeviceToken.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Sélectionne le sérialiseur en fonction de l'action."""
        if self.action == 'create':
            return DeviceTokenCreateSerializer
        return DeviceTokenSerializer
    
    def create(self, request, *args, **kwargs):
        """Enregistre un nouveau token pour l'utilisateur courant."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            token = DeviceTokenService.register_device(
                user_id=str(request.user.id),
                token=serializer.validated_data['token'],
                platform=serializer.validated_data['platform'],
                device_id=serializer.validated_data.get('device_id'),
                device_name=serializer.validated_data.get('device_name'),
                app_version=serializer.validated_data.get('app_version')
            )
            
            output_serializer = DeviceTokenSerializer(token)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except (ResourceNotFoundError, ValidationError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Désactive un token au lieu de le supprimer."""
        try:
            token = self.get_object()
            token.deactivate()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def deactivate_by_device(self, request):
        """
        Désactive tous les tokens associés à un appareil spécifique.
        
        Paramètres:
            device_id: ID de l'appareil
        """
        device_id = request.data.get('device_id')
        if not device_id:
            return Response(
                {'error': 'Le paramètre device_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            count = DeviceTokenService.deactivate_tokens_by_device_id(
                device_id=device_id,
                user_id=str(request.user.id)
            )
            
            return Response({
                'message': f'{count} token(s) désactivé(s) avec succès',
                'count': count
            })
            
        except ResourceNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST) 