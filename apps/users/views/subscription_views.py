"""
Vues pour la gestion des abonnements utilisateurs.
"""
import json
import logging
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.users.serializers.subscription_serializer import (
    SubscriptionSerializer,
    SubscriptionPlanSerializer,
    SubscriptionTransactionSerializer,
    SubscriptionCheckoutSerializer,
    SubscriptionCancelSerializer,
    AutoRenewSerializer
)
from apps.users.services.subscription_service import SubscriptionService
from apps.users.services.payment_service import PaymentService
from apps.core.exceptions import ValidationError, ResourceNotFoundError, PaymentError
from apps.core.permissions import IsOwnerOrAdmin

logger = logging.getLogger(__name__)

class SubscriptionPlanViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    ViewSet pour la récupération des plans d'abonnement disponibles.
    """
    permission_classes = []  # Accessible sans authentification
    
    def list(self, request):
        """
        Liste les plans d'abonnement disponibles.
        
        GET /subscriptions/plans
        """
        plans = [
            {
                "id": "FREE",
                "name": "Gratuit",
                "price": 0,
                "currency": "EUR",
                "billing_cycle": "NONE",
                "features": [
                    {
                        "name": "Création de projets",
                        "description": "Nombre de projets pouvant être créés",
                        "included": True,
                        "limit": 2
                    },
                    {
                        "name": "Messages",
                        "description": "Nombre de messages pouvant être envoyés par jour",
                        "included": True,
                        "limit": 10
                    },
                    {
                        "name": "Recherche avancée",
                        "description": "Accès aux filtres de recherche avancée",
                        "included": False,
                        "limit": None
                    },
                    {
                        "name": "Mise en avant",
                        "description": "Projets mis en avant dans les résultats de recherche",
                        "included": False,
                        "limit": None
                    }
                ]
            },
            {
                "id": "PREMIUM_MONTHLY",
                "name": "Premium Mensuel",
                "price": 9.99,
                "currency": "EUR",
                "billing_cycle": "MONTHLY",
                "features": [
                    {
                        "name": "Création de projets",
                        "description": "Nombre de projets pouvant être créés",
                        "included": True,
                        "limit": 10
                    },
                    {
                        "name": "Messages",
                        "description": "Nombre de messages pouvant être envoyés par jour",
                        "included": True,
                        "limit": 100
                    },
                    {
                        "name": "Recherche avancée",
                        "description": "Accès aux filtres de recherche avancée",
                        "included": True,
                        "limit": None
                    },
                    {
                        "name": "Mise en avant",
                        "description": "Projets mis en avant dans les résultats de recherche",
                        "included": True,
                        "limit": 1
                    }
                ]
            },
            {
                "id": "PREMIUM_YEARLY",
                "name": "Premium Annuel",
                "price": 99.99,
                "currency": "EUR",
                "billing_cycle": "YEARLY",
                "features": [
                    {
                        "name": "Création de projets",
                        "description": "Nombre de projets pouvant être créés",
                        "included": True,
                        "limit": None
                    },
                    {
                        "name": "Messages",
                        "description": "Nombre de messages pouvant être envoyés par jour",
                        "included": True,
                        "limit": None
                    },
                    {
                        "name": "Recherche avancée",
                        "description": "Accès aux filtres de recherche avancée",
                        "included": True,
                        "limit": None
                    },
                    {
                        "name": "Mise en avant",
                        "description": "Projets mis en avant dans les résultats de recherche",
                        "included": True,
                        "limit": 3
                    }
                ]
            }
        ]
        
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({"plans": serializer.data})


class SubscriptionViewSet(viewsets.GenericViewSet):
    """
    ViewSet pour la gestion des abonnements.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer
    
    @action(detail=False, methods=['get'], url_path='me')
    def my_subscription(self, request):
        """
        Récupère l'abonnement de l'utilisateur connecté.
        
        GET /subscriptions/me
        """
        try:
            subscription = SubscriptionService.get_user_subscription(request.user.id)
            
            if not subscription:
                # Si l'utilisateur n'a pas d'abonnement, retourner un abonnement gratuit par défaut
                data = {
                    "plan": "FREE",
                    "status": "ACTIVE",
                    "start_date": request.user.date_joined,
                    "end_date": None,
                    "auto_renew": False,
                    "payment_provider": None,
                    "payment_id": None,
                    "transactions": []
                }
                return Response(data)
            
            # Récupérer les transactions si l'abonnement existe
            transactions = SubscriptionService.get_subscription_transactions(
                subscription.id, 
                request.user.id
            )
            
            # Sérialiser l'abonnement avec les transactions
            serializer = SubscriptionSerializer(subscription)
            data = serializer.data
            
            # Ajouter les transactions à la réponse
            transaction_serializer = SubscriptionTransactionSerializer(transactions, many=True)
            data['transactions'] = transaction_serializer.data
            
            return Response(data)
            
        except ResourceNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """
        Initialise un paiement pour un abonnement Premium.
        
        POST /subscriptions/checkout
        """
        serializer = SubscriptionCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = serializer.validated_data.get('plan')
            return_url = serializer.validated_data.get('return_url')
            
            # Initialiser le paiement
            checkout_info = SubscriptionService.init_subscription_payment(
                user_id=request.user.id,
                plan=plan,
                return_url=return_url
            )
            
            return Response(checkout_info)
            
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PaymentError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'initialisation du paiement: {str(e)}")
            return Response(
                {"error": "Une erreur s'est produite lors de l'initialisation du paiement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['put'], url_path='me/auto-renew')
    def update_auto_renew(self, request):
        """
        Activation/désactivation du renouvellement automatique.
        
        PUT /subscriptions/me/auto-renew
        """
        serializer = AutoRenewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer l'abonnement actuel
            subscription = SubscriptionService.get_user_subscription(request.user.id)
            
            if not subscription:
                return Response(
                    {"error": "Aucun abonnement actif trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Mettre à jour le renouvellement automatique
            auto_renew = serializer.validated_data.get('auto_renew')
            updated_subscription = SubscriptionService.update_auto_renewal(
                subscription_id=subscription.id,
                user_id=request.user.id,
                auto_renew=auto_renew
            )
            
            return Response({
                "auto_renew": updated_subscription.auto_renew,
                "updated_at": updated_subscription.updated_at
            })
            
        except (ValidationError, ResourceNotFoundError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='me/cancel')
    def cancel_subscription(self, request):
        """
        Annulation de l'abonnement actuel.
        
        POST /subscriptions/me/cancel
        """
        serializer = SubscriptionCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer l'abonnement actuel
            subscription = SubscriptionService.get_user_subscription(request.user.id)
            
            if not subscription:
                return Response(
                    {"error": "Aucun abonnement actif trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Annuler l'abonnement
            cancel_reason = serializer.validated_data.get('cancel_reason')
            cancelled_subscription = SubscriptionService.cancel_subscription(
                subscription_id=subscription.id,
                user_id=request.user.id,
                cancel_reason=cancel_reason
            )
            
            return Response({
                "status": "CANCELLED",
                "end_date": cancelled_subscription.end_date,
                "message": "Votre abonnement a été annulé. Vous pouvez continuer à utiliser les fonctionnalités Premium jusqu'à la date de fin."
            })
            
        except (ValidationError, ResourceNotFoundError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionWebhookView(APIView):
    """
    Endpoint pour recevoir les webhooks de paiement.
    """
    permission_classes = []  # Pas d'authentification pour les webhooks
    
    def post(self, request):
        """
        Traite les webhooks de paiement.
        
        POST /webhooks/subscriptions
        """
        # Récupérer le contenu de la requête
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-My-CoolPay-Signature', '')
        
        try:
            # Vérifier la signature du webhook
            payment_service = PaymentService()
            
            if not payment_service.verify_webhook_signature(payload, signature):
                logger.warning("Signature de webhook invalide")
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            
            # Parser le payload
            event_data = json.loads(payload)
            event_type = event_data.get('type')
            
            if not event_type:
                logger.error("Type d'événement manquant dans le webhook")
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            # Traiter l'événement
            success = SubscriptionService.process_payment_webhook(event_type, event_data)
            
            if success:
                return Response(status=status.HTTP_200_OK)
            else:
                logger.error(f"Échec du traitement du webhook {event_type}")
                return Response(status=status.HTTP_400_BAD_REQUEST)
                
        except json.JSONDecodeError:
            logger.error("Payload de webhook JSON invalide")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 