"""
Vues pour la gestion des tokens d'authentification.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.translation import gettext_lazy as _

from apps.users.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class CustomTokenRefreshView(APIView):
    """Vue pour rafraîchir un token d'accès."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {"error": _("Le token de rafraîchissement est requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Utiliser le service d'authentification pour rafraîchir le token
            access_token, new_refresh_token = AuthService.refresh_token(refresh_token)
            
            return Response({
                "access": access_token,
                "refresh": new_refresh_token
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            logger.warning(f"Erreur de rafraîchissement de token: {str(e)}")
            return Response(
                {"error": _("Token de rafraîchissement invalide ou expiré.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors du rafraîchissement de token: {str(e)}")
            return Response(
                {"error": _("Une erreur est survenue lors du rafraîchissement du token.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 