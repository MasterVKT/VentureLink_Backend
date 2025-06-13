"""
Vues pour l'application core.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.services.currency_service import CurrencyService


class CurrencyListView(APIView):
    """
    Vue pour récupérer la liste des devises disponibles.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Récupère la liste des devises disponibles.
        
        GET /api/v1/currencies
        """
        currency_service = CurrencyService()
        currencies = currency_service.get_available_currencies()
        
        # Formater les données pour l'API
        currency_list = [
            {
                'code': code,
                'name': name,
                'symbol': currency_service.format_currency(1, code).strip('1.00 ')
            }
            for code, name in currencies.items()
        ]
        
        return Response({
            'currencies': currency_list,
            'default_currency': currency_service.default_currency
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def test_sentry(request):
    """
    Vue de test pour Sentry. Génère une exception qui sera capturée par Sentry.
    À utiliser uniquement à des fins de test.
    """
    try:
        division_by_zero = 1 / 0
    except Exception as e:
        # Journaliser l'erreur et la faire capturer par Sentry
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Test Sentry - Division par zéro intentionnelle", exc_info=True)
        return Response(
            {"error": "Test Sentry exécuté avec succès. Une exception a été générée et envoyée à Sentry."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 