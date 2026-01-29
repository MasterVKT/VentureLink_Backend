"""
Vues API pour la gestion des paiements.
"""
import json
import logging
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from rest_framework import viewsets, mixins, status, filters, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from apps.payments.models import (
    Payment, Refund, PaymentStatus,
    SubscriptionPlan, UserSubscription  # ✅ Nouveaux modèles unifiés
)
from apps.payments.serializers import (
    PaymentSerializer, PaymentCreateSerializer,
    RefundSerializer, RefundCreateSerializer,
    SubscriptionPlanSerializer, UserSubscriptionSerializer  # ✅ Nouveaux serializers
)
from apps.payments.services.payment_service import PaymentService
from apps.payments.services.mycoolpay_service import get_mycoolpay_service, MyCoolPayError
from apps.core.permissions import IsAdminUser
from apps.payments.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class PaymentViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    API endpoint pour la gestion des paiements.
    
    list:
        Récupère la liste des paiements de l'utilisateur connecté.
        
    retrieve:
        Récupère les détails d'un paiement spécifique.
        
    create_payment:
        Crée un nouveau paiement.
        
    refund:
        Rembourse un paiement existant.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_type', 'is_test']
    ordering_fields = ['created_at', 'completed_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les paiements de l'utilisateur connecté ou tous les paiements pour un admin."""
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Retourne le serializer approprié en fonction de l'action."""
        if self.action == 'create_payment':
            return PaymentCreateSerializer
        elif self.action == 'refund':
            return RefundCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """
        Crée un nouveau paiement et retourne l'URL de paiement.
        
        Cette méthode crée un paiement en fonction des données fournies
        et retourne les informations nécessaires pour rediriger l'utilisateur
        vers la page de paiement My-CoolPay.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Créer le paiement via le service
            payment = PaymentService.create_payment(
                user=request.user,
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                description=serializer.validated_data['description'],
                payment_type=serializer.validated_data['payment_type'],
                metadata=serializer.validated_data.get('metadata'),
                success_url=serializer.validated_data.get('success_url'),
                cancel_url=serializer.validated_data.get('cancel_url'),
                statement_descriptor=serializer.validated_data.get('statement_descriptor'),
                is_test=not settings.MYCOOLPAY_LIVE_MODE
            )
            
            # Retourner l'URL de paiement et les informations du paiement
            return Response({
                'payment': PaymentSerializer(payment).data,
                'checkout_url': payment.external_checkout_url
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du paiement: {str(e)}")
            return Response({
                'error': _("Une erreur est survenue lors de la création du paiement.")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Rembourse un paiement existant.
        
        Cette méthode permet de rembourser partiellement ou totalement un paiement.
        Si le montant n'est pas spécifié, le remboursement est total.
        """
        payment = self.get_object()
        
        # Vérifier que le paiement peut être remboursé
        if not payment.can_be_refunded:
            return Response({
                'error': _("Ce paiement ne peut pas être remboursé.")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Effectuer le remboursement via le service
            payment, refund = PaymentService.refund_payment(
                payment_id=str(payment.id),
                amount=serializer.validated_data.get('amount'),
                reason=serializer.validated_data.get('reason'),
                notes=serializer.validated_data.get('notes')
            )
            
            # Retourner les informations du remboursement
            return Response({
                'payment': PaymentSerializer(payment).data,
                'refund': RefundSerializer(refund).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du remboursement du paiement {payment.id}: {str(e)}")
            return Response({
                'error': _("Une erreur est survenue lors du remboursement.")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def check_status(self, request, pk=None):
        """
        Met à jour et retourne le statut actuel d'un paiement.
        
        Cette méthode interroge My-CoolPay pour obtenir le statut le plus récent
        du paiement et le met à jour dans la base de données.
        """
        payment = self.get_object()
        
        try:
            # Mettre à jour le statut via le service
            updated_payment = PaymentService.update_payment_status(str(payment.id))
            
            # Retourner le paiement mis à jour
            return Response(PaymentSerializer(updated_payment).data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut du paiement {payment.id}: {str(e)}")
            return Response({
                'error': _("Une erreur est survenue lors de la vérification du statut du paiement.")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WebhookViewSet(viewsets.ViewSet):
    """
    API endpoint pour les webhooks My-CoolPay.
    
    Cette vue gère les callbacks envoyés par My-CoolPay
    pour les événements liés aux paiements.
    """
    permission_classes = []  # Pas d'authentification requise pour les webhooks
    
    @transaction.atomic
    def create(self, request):
        """
        Traite les événements webhook envoyés par My-CoolPay.
        
        Cette méthode vérifie la signature de l'événement, puis le traite
        en fonction de son type (mise à jour de paiement, remboursement, etc.).
        """
        # Vérifier la signature du webhook si configuré
        if settings.MYCOOLPAY_WEBHOOK_SECRET:
            # La vérification serait implémentée ici avec le secret
            # Si la vérification échoue, retourner une erreur 401
            pass
        
        try:
            # Traiter l'événement
            payment = PaymentService.handle_webhook_event(request.data)
            
            # Simplement retourner un 200 OK pour confirmer la réception
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook My-CoolPay: {str(e)}")
            # On retourne quand même un 200 pour éviter les retentatives
            # La plupart des services de paiement préfèrent que l'on confirme
            # la réception même en cas d'erreur
            return Response({'status': 'error'}, status=status.HTTP_200_OK)


class SubscriptionPlanListView(generics.ListAPIView):
    """Liste des plans d'abonnement disponibles"""
    
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price_xaf')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserSubscriptionView(generics.RetrieveAPIView):
    """Récupérer l'abonnement actuel de l'utilisateur"""
    
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        try:
            return UserSubscription.objects.get(
                user=self.request.user,
                status__in=['ACTIVE', 'TRIAL']
            )
        except UserSubscription.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        subscription = self.get_object()
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        else:
            return Response({
                'message': 'Aucun abonnement actif',
                'has_subscription': False
            })


class PaymentHistoryView(generics.ListAPIView):
    """Historique des paiements de l'utilisateur"""
    
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_subscription_payment(request):
    """
    Créer un paiement pour un abonnement
    
    POST /api/v1/payments/subscription/create/
    Body: {
        "plan_id": "uuid",
        "phone_number": "+237699999999"  // Obligatoire
    }
    """
    try:
        plan_id = request.data.get('plan_id')
        phone_number = request.data.get('phone_number')
        
        if not plan_id:
            return Response({
                'error': 'plan_id requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not phone_number:
            return Response({
                'error': 'phone_number requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Plan d\'abonnement non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        has_active_subscription = UserSubscription.objects.filter(
            user=request.user,
            status__in=['ACTIVE', 'TRIAL']
        ).exists()
        
        if has_active_subscription:
            return Response({
                'error': 'Vous avez déjà un abonnement actif'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtenir la devise de l'utilisateur ou utiliser XAF par défaut
        currency = getattr(request.user, 'preferred_currency', 'XAF') or 'XAF'
        
        # Créer le paiement via My-CoolPay (version simplifiée)
        mycoolpay_service = get_mycoolpay_service()
        
        success, message, payment_data = mycoolpay_service.process_subscription_payment(
            user=request.user,
            subscription_plan=plan,
            phone_number=phone_number,  # Numéro fourni par le frontend
            currency=currency
        )
        
        if success:
            return Response({
                'message': message,
                'payment_id': payment_data['payment_id'],
                'payment_url': payment_data['payment_url'],
                'transaction_ref': payment_data['transaction_ref'],
                'plan': SubscriptionPlanSerializer(plan).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erreur lors de la création du paiement d'abonnement: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Fonction supprimée - Paiements directs remplacés par My-CoolPay paylinks uniquement


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def authorize_payment_otp(request):
    """
    Autoriser un paiement avec code OTP
    
    POST /api/v1/payments/authorize/
    Body: {
        "payment_id": 123,
        "otp_code": "123456"
    }
    """
    try:
        payment_id = request.data.get('payment_id')
        otp_code = request.data.get('otp_code')
        
        if not all([payment_id, otp_code]):
            return Response({
                'error': 'payment_id et otp_code requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le paiement
        try:
            payment = Payment.objects.get(
                id=payment_id,
                user=request.user,
                status=PaymentStatus.PENDING
            )
        except Payment.DoesNotExist:
            return Response({
                'error': 'Paiement non trouvé ou déjà traité'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Autoriser le paiement
        mycoolpay_service = get_mycoolpay_service()
        
        response = mycoolpay_service.authorize_payin(
            transaction_ref=payment.external_reference,
            otp_code=otp_code
        )
        
        return Response({
            'message': 'Code OTP soumis avec succès',
            'action': response.get('action'),
            'ussd': response.get('ussd'),
            'transaction_ref': payment.external_reference
        })
        
    except MyCoolPayError as e:
        return Response({
            'error': f'Erreur My-CoolPay: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de l'autorisation OTP: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_payment_status(request, payment_id):
    """
    Vérifier le statut d'un paiement
    
    GET /api/v1/payments/{payment_id}/status/
    """
    try:
        # Vérifier le paiement
        try:
            payment = Payment.objects.get(
                id=payment_id,
                user=request.user
            )
        except Payment.DoesNotExist:
            return Response({
                'error': 'Paiement non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier le statut via My-CoolPay si nécessaire
        if payment.status == PaymentStatus.PENDING and payment.external_reference:
            mycoolpay_service = get_mycoolpay_service()
            
            try:
                response = mycoolpay_service.check_transaction_status(payment.external_reference)
                
                # Mettre à jour le statut local
                api_status = response.get('transaction_status')
                if api_status == 'SUCCESS':
                    payment.status = PaymentStatus.COMPLETED
                    payment.save()
                elif api_status == 'FAILED':
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                elif api_status == 'CANCELED':
                    payment.status = PaymentStatus.CANCELLED
                    payment.save()
                    
            except MyCoolPayError:
                # Ignorer les erreurs de vérification
                pass
        
        return Response({
            'payment_id': payment.id,
            'status': payment.status,
            'amount': payment.amount,
            'currency': payment.currency,
            'description': payment.description,
            'created_at': payment.created_at,
            'completed_at': payment.completed_at
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_payment_methods(request):
    """
    Obtenir la liste des méthodes de paiement disponibles (Seulement My-CoolPay)
    
    GET /api/v1/payments/methods/
    """
    mycoolpay_service = get_mycoolpay_service()
    
    methods = [
        {
            'code': 'MYCOOLPAY',
            'name': 'My-CoolPay',
            'description': 'Paiement sécurisé via My-CoolPay (Orange Money, MTN Mobile Money, Cartes bancaires)',
            'type': 'paylink',
            'supports_all_operators': True
        }
    ]
    
    return Response({
        'methods': methods,
        'supported_currencies': mycoolpay_service.SUPPORTED_CURRENCIES,
        'message': 'My-CoolPay prend en charge tous les opérateurs de paiement mobile et cartes bancaires'
    })


@csrf_exempt
@require_http_methods(["POST"])
def mycoolpay_callback(request):
    """
    Endpoint de callback pour My-CoolPay
    
    POST /api/v1/payments/mycoolpay/callback/
    """
    try:
        # Obtenir l'IP du client
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Vérifier l'IP (optionnel en mode debug)
        mycoolpay_service = get_mycoolpay_service()
        
        if not settings.DEBUG:
            if not mycoolpay_service.verify_callback_ip(ip):
                logger.warning(f"Callback de IP non autorisée: {ip}")
                return HttpResponse("Forbidden", status=403)
        
        # Parser les données JSON
        try:
            callback_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.warning("Données de callback JSON invalides")
            return HttpResponse("Bad Request", status=400)
        
        # Traiter le callback
        success = mycoolpay_service.handle_payment_callback(callback_data)
        
        if success:
            return HttpResponse("OK", status=200)
        else:
            return HttpResponse("Bad Request", status=400)
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du callback: {str(e)}")
        return HttpResponse("Internal Server Error", status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """
    Annuler l'abonnement actuel
    
    POST /api/v1/payments/subscription/cancel/
    """
    try:
        # Trouver l'abonnement actif
        try:
            subscription = UserSubscription.objects.get(
                user=request.user,
                status__in=['ACTIVE', 'TRIAL']
            )
        except UserSubscription.DoesNotExist:
            return Response({
                'error': 'Aucun abonnement actif trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Annuler l'abonnement en utilisant la méthode du modèle
        reason = request.data.get('reason', 'Annulation par l\'utilisateur')
        subscription.cancel(reason=reason)
        
        # Envoyer une notification
        from apps.notifications.services.notification_service import NotificationService
        
        NotificationService.create_from_template(
            template_code='subscription_cancelled',
            recipient=request.user,
            context_data={
                'plan_name': subscription.plan.name
            }
        )
        
        return Response({
            'message': 'Abonnement annulé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de l'abonnement: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_account_balance(request):
    """
    Obtenir le solde du compte My-CoolPay (pour les admins)
    
    GET /api/v1/payments/balance/
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Accès non autorisé'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        mycoolpay_service = get_mycoolpay_service()
        balance_data = mycoolpay_service.get_balance()
        
        return Response(balance_data)
        
    except MyCoolPayError as e:
        return Response({
            'error': f'Erreur My-CoolPay: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du solde: {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def mycoolpay_webhook(request):
    """
    Point de terminaison pour les webhooks My-CoolPay.
    
    Reçoit et traite les événements de webhook envoyés par My-CoolPay
    pour mettre à jour les statuts des paiements et abonnements.
    """
    # Récupérer les données du webhook
    try:
        payload = request.body.decode('utf-8')
        event_data = json.loads(payload)
    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid JSON payload"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Récupérer la signature du webhook
    signature = request.META.get('HTTP_X_MYCOOLPAY_SIGNATURE', '')
    
    # Vérifier la signature
    webhook_secret = settings.MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET
    if settings.PAYMENT_SANDBOX_MODE:
        webhook_secret = settings.MYCOOLPAY_SANDBOX_WEBHOOK_SECRET
    
    if not WebhookService.verify_signature(payload, signature, webhook_secret):
        logger.warning("Signature de webhook My-CoolPay invalide")
        return Response(
            {"error": "Invalid signature"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Journaliser la réception de l'événement
    logger.info(f"Webhook My-CoolPay reçu: {event_data.get('event_type', 'unknown')}")
    
    # Traiter l'événement
    success = WebhookService.process_webhook_event(event_data)
    
    if success:
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    else:
        return Response(
            {"status": "error", "message": "Event processing failed"},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        ) 