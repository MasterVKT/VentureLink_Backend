"""
Vue API pour l'initiation de paiement d'investissement (Tâche B3.2).

Endpoint : POST /api/v1/payments/initiate/

Permet à un investisseur d'initier le paiement d'un investissement existant
via My-CoolPay. Retourne un lien de paiement vers lequel rediriger l'utilisateur.
"""
import logging
import uuid
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.payments.models import Payment
from apps.payments.serializers.investment_payment_serializers import (
    InitiateInvestmentPaymentSerializer,
    InvestmentPaymentResponseSerializer,
)
from apps.payments.serializers import PaymentSerializer
from apps.payments.services.mycoolpay_service import get_mycoolpay_service, MyCoolPayError
from apps.investments.models import Investment

logger = logging.getLogger(__name__)

# Durée de validité du lien de paiement My-CoolPay
PAYMENT_LINK_EXPIRY_HOURS = 1


class InitiateInvestmentPaymentView(APIView):
    """
    Initier un paiement d'investissement via My-CoolPay.

    Crée un paylink My-CoolPay pour un investissement existant et retourne
    l'URL de paiement vers laquelle rediriger l'utilisateur.

    L'investissement passe au statut APPROVED (en attente de confirmation
    de paiement via webhook).

    Après paiement réussi, le webhook My-CoolPay met automatiquement à jour :
    - Le statut du Payment → COMPLETED
    - Le statut de l'Investment → COMPLETED
    - Le funding_raised du Project
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Initier un paiement d'investissement",
        operation_description=(
            "Crée un lien de paiement My-CoolPay pour un investissement existant. "
            "L'utilisateur doit être redirigé vers `payment_url` pour finaliser le paiement. "
            "Le lien expire après 1 heure. "
            "Une fois le paiement confirmé par My-CoolPay (webhook), "
            "l'investissement passe automatiquement au statut COMPLETED."
        ),
        request_body=InitiateInvestmentPaymentSerializer,
        responses={
            201: openapi.Response(
                description="Lien de paiement créé avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'payment_id': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format='uuid',
                            description="ID du paiement créé en base",
                        ),
                        'payment_url': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="URL My-CoolPay — rediriger l'utilisateur ici",
                        ),
                        'transaction_ref': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Référence de transaction My-CoolPay",
                        ),
                        'investment_id': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format='uuid',
                        ),
                        'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'currency': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Statut du paiement (toujours PENDING à la création)",
                        ),
                        'expires_at': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format='date-time',
                            description="Date d'expiration du lien (1 heure)",
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Données invalides",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            402: openapi.Response(
                description="Erreur My-CoolPay lors de la création du lien",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            500: "Erreur interne du serveur",
        },
        tags=['Paiements — Investissements'],
    )
    def post(self, request):
        """
        POST /api/v1/payments/initiate/

        Body:
        {
            "investment_id": "<uuid>",
            "phone_number": "+237690000000",
            "currency": "XAF"
        }

        Réponse (201):
        {
            "payment_id": "<uuid>",
            "payment_url": "https://pay.my-coolpay.com/...",
            "transaction_ref": "MCP-...",
            "investment_id": "<uuid>",
            "amount": 50000.00,
            "currency": "XAF",
            "status": "PENDING",
            "expires_at": "2026-05-30T11:00:00Z",
            "message": "Paiement initié. Redirigez l'utilisateur vers payment_url."
        }
        """
        # 1. Valider les données d'entrée
        serializer = InitiateInvestmentPaymentSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Récupérer l'investissement validé (pas de requête DB supplémentaire)
        investment = serializer.get_investment()
        currency = serializer.validated_data.get('currency', 'XAF')
        phone_number = serializer.validated_data['phone_number']

        # 3. Générer une référence unique pour cette transaction
        reference = f"INV-{investment.id}-{uuid.uuid4().hex[:8].upper()}"

        # 4. Construire l'URL de callback
        callback_url = request.build_absolute_uri(
            '/api/v1/payments/mycoolpay/webhook/'
        )

        # 5. Obtenir le montant dans la devise demandée
        # Le montant est stocké dans investment.amount (MoneyField)
        amount = investment.amount

        # 6. Initier le paiement via My-CoolPay
        mycoolpay = get_mycoolpay_service()

        try:
            mcp_response = mycoolpay.create_paylink({
                'transaction_amount': int(amount),
                'transaction_currency': currency,
                'transaction_reason': (
                    f"Investissement dans {investment.project.title}"
                ),
                'app_transaction_ref': reference,
                'customer_phone_number': phone_number,
                'customer_name': (
                    request.user.get_full_name() or request.user.email
                ),
                'customer_email': request.user.email,
                'customer_lang': 'fr',
                'callback_url': callback_url,
            })
        except MyCoolPayError as exc:
            logger.error(
                f"B3.2 — Erreur My-CoolPay pour investissement {investment.id}: {exc}"
            )
            return Response(
                {'error': str(exc)},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        payment_url = mcp_response.get('payment_url', '')
        transaction_ref = mcp_response.get('transaction_ref', '')
        expires_at = timezone.now() + timedelta(hours=PAYMENT_LINK_EXPIRY_HOURS)

        # 7. Créer l'enregistrement Payment en base
        #    Lier le Payment à l'Investment via GenericForeignKey
        content_type = ContentType.objects.get_for_model(Investment)

        payment = Payment.objects.create(
            user=request.user,
            amount=amount,
            currency=currency,
            payment_type=Payment.PaymentType.INVESTMENT,
            status=Payment.PaymentStatus.PENDING,
            external_payment_id=transaction_ref,
            external_checkout_url=payment_url,
            description=f"Investissement dans {investment.project.title}",
            is_test=mycoolpay.sandbox,
            content_type=content_type,
            object_id=investment.id,
            metadata={
                'investment_id': str(investment.id),
                'project_id': str(investment.project.id),
                'project_title': investment.project.title,
                'reference': reference,
                'phone_number': phone_number,
                'expires_at': expires_at.isoformat(),
            },
        )

        # 8. Mettre à jour le statut de l'investissement → APPROVED
        #    (en attente de confirmation de paiement via webhook)
        investment.status = Investment.STATUS_APPROVED
        investment.save(update_fields=['status', 'updated_at'])

        logger.info(
            f"B3.2 — Paiement investissement initié: "
            f"user={request.user.id} "
            f"investment={investment.id} "
            f"payment={payment.id} "
            f"ref={transaction_ref} "
            f"montant={amount} {currency}"
        )

        # 9. Retourner la réponse
        return Response(
            {
                'payment_id': str(payment.id),
                'payment_url': payment_url,
                'transaction_ref': transaction_ref,
                'investment_id': str(investment.id),
                'amount': float(amount),
                'currency': currency,
                'status': payment.status,
                'expires_at': expires_at.isoformat(),
                'message': (
                    "Paiement initié. Redirigez l'utilisateur vers payment_url."
                ),
            },
            status=status.HTTP_201_CREATED,
        )
