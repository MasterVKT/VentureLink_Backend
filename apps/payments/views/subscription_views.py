"""
Vues API pour la gestion des abonnements.
Sprint 3 - B3.4 : Système Abonnements
Sprint 3 - B3.6 : Logs et Sécurité (rate limiting + audit trail)
"""
import logging
from django.utils import timezone
from django.db import transaction

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.payments.models import SubscriptionPlan, UserSubscription
from apps.payments.serializers.subscription_serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionCreateSerializer,
    SubscriptionUpgradeSerializer,
)
from apps.payments.services.mycoolpay_service import get_mycoolpay_service
# B3.6 — Sécurité et audit trail
from apps.payments.services.security_service import (
    PaymentSecurityService,
    PaymentAuditLogger,
)
# Notifications (import au niveau module pour permettre le mock dans les tests)
from apps.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(generics.ListAPIView):
    """
    GET /api/v1/payments/plans/
    Liste tous les plans d'abonnement actifs, triés par ordre d'affichage.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubscriptionPlanDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/payments/plans/<plan_id>/
    Détails d'un plan d'abonnement spécifique.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


class CurrentUserSubscriptionView(generics.RetrieveAPIView):
    """
    GET /api/v1/payments/subscription/
    Récupère l'abonnement actif de l'utilisateur connecté.
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return UserSubscription.objects.filter(
            user=self.request.user,
            status__in=[
                UserSubscription.SubscriptionStatus.ACTIVE,
                UserSubscription.SubscriptionStatus.TRIAL,
            ]
        ).select_related('plan').first()

    def retrieve(self, request, *args, **kwargs):
        subscription = self.get_object()
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)

        free_plan = SubscriptionPlan.objects.filter(id='free', is_active=True).first()
        return Response({
            'has_subscription': False,
            'message': 'Aucun abonnement actif. Vous utilisez le plan gratuit.',
            'free_plan': SubscriptionPlanSerializer(free_plan).data if free_plan else None,
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def subscribe_to_plan(request):
    """
    POST /api/v1/payments/subscription/subscribe/

    Souscrire à un plan d'abonnement.

    Body:
    {
        "plan_id": "basic_monthly",
        "billing_currency": "XAF",
        "phone_number": "+237690000000",
        "start_trial": true
    }
    """
    serializer = UserSubscriptionCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if not serializer.is_valid():
        logger.warning(
            "Tentative de souscription invalide par %s: %s",
            request.user.email, serializer.errors
        )
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    plan_id = serializer.validated_data['plan_id']
    billing_currency = serializer.validated_data.get('billing_currency', 'XAF')
    start_trial = serializer.validated_data.get('start_trial', True)
    phone_number = request.data.get('phone_number', '')

    # B3.6 — Rate limiting souscriptions
    ip_address = PaymentSecurityService.get_client_ip(request)
    allowed, rate_error = PaymentSecurityService.rate_limiter.check_subscription_attempts(request.user)
    if not allowed:
        return Response({'error': rate_error}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': "Plan d'abonnement introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # Vérifier si l'utilisateur a déjà un abonnement actif
    existing = UserSubscription.objects.filter(
        user=request.user,
        status__in=[
            UserSubscription.SubscriptionStatus.ACTIVE,
            UserSubscription.SubscriptionStatus.TRIAL,
        ]
    ).first()

    if existing:
        logger.info(
            "Utilisateur %s a déjà un abonnement actif (%s).",
            request.user.email, existing.plan.name
        )
        return Response(
            {
                'error': 'Vous avez déjà un abonnement actif.',
                'current_plan': existing.plan.name,
                'hint': 'Utilisez /subscription/upgrade/ pour changer de plan.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Plan gratuit — activation directe sans paiement
    if plan.is_free:
        with transaction.atomic():
            subscription = UserSubscription.create_subscription(
                user=request.user,
                plan=plan,
                billing_currency=billing_currency,
                start_trial=False,
            )
            subscription.activate()

        # B3.6 — Audit trail souscription gratuite
        PaymentAuditLogger.log_subscription_action(
            user=request.user,
            action='subscribed_free',
            plan_name=plan.name,
            ip_address=ip_address,
        )
        logger.info("Utilisateur %s souscrit au plan gratuit %s.", request.user.email, plan.name)
        return Response(
            {
                'message': f'Abonnement {plan.name} activé avec succès.',
                'subscription': UserSubscriptionSerializer(subscription).data,
                'payment_required': False,
            },
            status=status.HTTP_201_CREATED
        )

    # Plan payant — numéro de téléphone obligatoire
    if not phone_number:
        return Response(
            {'error': 'phone_number est requis pour les plans payants.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # B3.6 — Validation complète du paiement (devise + montant + téléphone)
    amount = plan.get_price_for_currency(billing_currency)
    is_valid, validation_error = PaymentSecurityService.validate_payment_request(
        user=request.user,
        amount=amount,
        currency=billing_currency,
        phone_number=phone_number,
        ip_address=ip_address,
    )
    if not is_valid:
        return Response({'error': validation_error}, status=status.HTTP_400_BAD_REQUEST)

    # Créer l'abonnement en statut PENDING
    with transaction.atomic():
        subscription = UserSubscription.create_subscription(
            user=request.user,
            plan=plan,
            billing_currency=billing_currency,
            start_trial=start_trial,
        )

    # Initier le paiement via My-CoolPay
    try:
        mycoolpay = get_mycoolpay_service()
        success, message, payment_data = mycoolpay.process_subscription_payment(
            user=request.user,
            subscription_plan=plan,
            phone_number=phone_number,
            currency=billing_currency,
        )
    except Exception as e:
        logger.exception("Erreur My-CoolPay lors de la souscription de %s: %s", request.user.email, e)
        subscription.delete()
        return Response(
            {'error': "Erreur lors de l'initiation du paiement. Veuillez réessayer."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if not success:
        subscription.delete()
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    subscription.mycoolpay_subscription_id = str(payment_data.get('payment_id', ''))
    subscription.save(update_fields=['mycoolpay_subscription_id'])

    # B3.6 — Audit trail souscription payante initiée
    PaymentAuditLogger.log_payment_initiated(
        user=request.user,
        amount=plan.get_price_for_currency(billing_currency),
        currency=billing_currency,
        reference=str(payment_data.get('transaction_ref', '')),
        ip_address=ip_address,
    )
    PaymentAuditLogger.log_subscription_action(
        user=request.user,
        action='subscribed_paid',
        plan_name=plan.name,
        ip_address=ip_address,
    )
    logger.info(
        "Souscription initiée pour %s — plan %s — paiement %s.",
        request.user.email, plan.name, payment_data.get('payment_id')
    )

    return Response(
        {
            'message': 'Souscription initiée. Complétez le paiement via le lien fourni.',
            'subscription': UserSubscriptionSerializer(subscription).data,
            'payment_required': True,
            'payment_url': payment_data.get('payment_url'),
            'payment_id': str(payment_data.get('payment_id', '')),
            'transaction_ref': payment_data.get('transaction_ref'),
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upgrade_subscription(request):
    """
    POST /api/v1/payments/subscription/upgrade/

    Changer de plan (upgrade ou downgrade).

    Body:
    {
        "new_plan_id": "premium_monthly",
        "billing_currency": "XAF",
        "phone_number": "+237690000000"
    }

    Règles :
    - Upgrade (plan plus cher) : paiement immédiat requis
    - Downgrade (plan moins cher) : effectif à la fin de la période actuelle
    - Passage au plan FREE : effectif immédiatement, sans paiement
    """
    serializer = SubscriptionUpgradeSerializer(
        data=request.data,
        context={'request': request}
    )

    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    new_plan_id = serializer.validated_data['new_plan_id']
    billing_currency = serializer.validated_data.get('billing_currency', 'XAF')
    phone_number = request.data.get('phone_number', '')

    # B3.6 — IP pour audit trail
    ip_address = PaymentSecurityService.get_client_ip(request)

    try:
        new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': "Plan d'abonnement introuvable."}, status=status.HTTP_404_NOT_FOUND)

    current_subscription = UserSubscription.objects.filter(
        user=request.user,
        status__in=[
            UserSubscription.SubscriptionStatus.ACTIVE,
            UserSubscription.SubscriptionStatus.TRIAL,
        ]
    ).select_related('plan').first()

    if not current_subscription:
        return Response(
            {'error': "Aucun abonnement actif. Utilisez /subscription/subscribe/ pour souscrire."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if current_subscription.plan.id == new_plan_id:
        return Response({'error': 'Vous êtes déjà sur ce plan.'}, status=status.HTTP_400_BAD_REQUEST)

    current_price = current_subscription.plan.get_price_for_currency(billing_currency)
    new_price = new_plan.get_price_for_currency(billing_currency)
    is_upgrade = new_price > current_price

    logger.info(
        "%s demandé par %s : %s → %s",
        'Upgrade' if is_upgrade else 'Downgrade',
        request.user.email,
        current_subscription.plan.name,
        new_plan.name
    )

    # Passage au plan FREE — effectif immédiatement
    if new_plan.is_free:
        with transaction.atomic():
            current_subscription.cancel(reason=f'Passage au plan gratuit {new_plan.name}')
            new_subscription = UserSubscription.create_subscription(
                user=request.user,
                plan=new_plan,
                billing_currency=billing_currency,
                start_trial=False,
            )
            new_subscription.activate()

        # B3.6 — Audit trail downgrade vers FREE
        PaymentAuditLogger.log_subscription_action(
            user=request.user,
            action='downgraded_to_free',
            plan_name=new_plan.name,
            ip_address=ip_address,
        )
        return Response({
            'message': f'Passage au plan {new_plan.name} effectué avec succès.',
            'subscription': UserSubscriptionSerializer(new_subscription).data,
            'payment_required': False,
            'effective': 'immediate',
        })

    # Downgrade — effectif à la fin de la période
    if not is_upgrade:
        current_subscription.metadata['pending_downgrade'] = {
            'new_plan_id': new_plan_id,
            'billing_currency': billing_currency,
            'requested_at': timezone.now().isoformat(),
        }
        current_subscription.auto_renew = False
        current_subscription.save(update_fields=['metadata', 'auto_renew'])

        # B3.6 — Audit trail downgrade programmé
        PaymentAuditLogger.log_subscription_action(
            user=request.user,
            action='downgrade_scheduled',
            plan_name=new_plan.name,
            ip_address=ip_address,
        )
        return Response({
            'message': (
                f'Downgrade vers {new_plan.name} programmé. '
                f'Votre plan actuel ({current_subscription.plan.name}) '
                f"reste actif jusqu'au {current_subscription.expires_at.strftime('%d/%m/%Y')}."
            ),
            'current_subscription': UserSubscriptionSerializer(current_subscription).data,
            'payment_required': False,
            'effective': 'end_of_period',
            'effective_date': current_subscription.expires_at.isoformat(),
        })

    # Upgrade — paiement immédiat
    if not phone_number:
        return Response(
            {'error': 'phone_number est requis pour un upgrade vers un plan payant.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # B3.6 — Validation complète avant paiement d'upgrade
    upgrade_amount = new_plan.get_price_for_currency(billing_currency)
    is_valid, validation_error = PaymentSecurityService.validate_payment_request(
        user=request.user,
        amount=upgrade_amount,
        currency=billing_currency,
        phone_number=phone_number,
        ip_address=ip_address,
    )
    if not is_valid:
        return Response({'error': validation_error}, status=status.HTTP_400_BAD_REQUEST)

    try:
        mycoolpay = get_mycoolpay_service()
        success, message, payment_data = mycoolpay.process_subscription_payment(
            user=request.user,
            subscription_plan=new_plan,
            phone_number=phone_number,
            currency=billing_currency,
        )
    except Exception as e:
        logger.exception("Erreur My-CoolPay lors de l'upgrade de %s: %s", request.user.email, e)
        return Response(
            {'error': "Erreur lors de l'initiation du paiement. Veuillez réessayer."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if not success:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    current_subscription.metadata['pending_upgrade'] = {
        'new_plan_id': new_plan_id,
        'billing_currency': billing_currency,
        'payment_id': str(payment_data.get('payment_id', '')),
        'requested_at': timezone.now().isoformat(),
    }
    current_subscription.save(update_fields=['metadata'])

    # B3.6 — Audit trail upgrade initié
    PaymentAuditLogger.log_payment_initiated(
        user=request.user,
        amount=new_plan.get_price_for_currency(billing_currency),
        currency=billing_currency,
        reference=str(payment_data.get('transaction_ref', '')),
        ip_address=ip_address,
    )
    PaymentAuditLogger.log_subscription_action(
        user=request.user,
        action='upgrade_initiated',
        plan_name=new_plan.name,
        ip_address=ip_address,
    )
    logger.info(
        "Upgrade initié pour %s — %s → %s — paiement %s.",
        request.user.email, current_subscription.plan.name, new_plan.name, payment_data.get('payment_id')
    )

    return Response({
        'message': 'Upgrade initié. Complétez le paiement via le lien fourni.',
        'current_subscription': UserSubscriptionSerializer(current_subscription).data,
        'new_plan': SubscriptionPlanSerializer(new_plan).data,
        'payment_required': True,
        'payment_url': payment_data.get('payment_url'),
        'payment_id': str(payment_data.get('payment_id', '')),
        'transaction_ref': payment_data.get('transaction_ref'),
        'effective': 'after_payment',
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_subscription(request):
    """
    POST /api/v1/payments/subscription/cancel/

    Annuler l'abonnement actif.
    L'accès reste actif jusqu'à la fin de la période payée.

    Body (optionnel):
    {
        "reason": "Raison de l'annulation"
    }
    """
    subscription = UserSubscription.objects.filter(
        user=request.user,
        status__in=[
            UserSubscription.SubscriptionStatus.ACTIVE,
            UserSubscription.SubscriptionStatus.TRIAL,
        ]
    ).select_related('plan').first()

    if not subscription:
        return Response({'error': "Aucun abonnement actif à annuler."}, status=status.HTTP_404_NOT_FOUND)

    reason = request.data.get('reason', "Annulation par l'utilisateur")
    subscription.cancel(reason=reason)

    # B3.6 — Audit trail annulation
    PaymentAuditLogger.log_subscription_action(
        user=request.user,
        action='cancelled',
        plan_name=subscription.plan.name,
        ip_address=PaymentSecurityService.get_client_ip(request),
    )
    logger.info(
        "Abonnement annulé pour %s — plan %s — raison : %s",
        request.user.email, subscription.plan.name, reason
    )

    try:
        NotificationService.create_from_template(
            template_code='subscription_cancelled',
            recipient=request.user,
            context_data={'plan_name': subscription.plan.name},
        )
    except Exception as e:
        logger.warning("Impossible d'envoyer la notification d'annulation : %s", e)

    return Response({
        'message': (
            f'Abonnement {subscription.plan.name} annulé. '
            f"Votre accès reste actif jusqu'au "
            f"{subscription.expires_at.strftime('%d/%m/%Y')}."
        ),
        'subscription': UserSubscriptionSerializer(subscription).data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_subscription_limits(request):
    """
    GET /api/v1/payments/subscription/limits/

    Retourne les limites du plan actif de l'utilisateur et leur utilisation.
    Utile pour le frontend pour afficher les quotas restants.
    """
    subscription = UserSubscription.objects.filter(
        user=request.user,
        status__in=[
            UserSubscription.SubscriptionStatus.ACTIVE,
            UserSubscription.SubscriptionStatus.TRIAL,
        ]
    ).select_related('plan').first()

    if subscription:
        plan = subscription.plan
    else:
        # Utiliser le plan FREE par défaut
        plan = SubscriptionPlan.objects.filter(id='free', is_active=True).first()
        if not plan:
            return Response({'error': "Aucun plan disponible."}, status=status.HTTP_404_NOT_FOUND)

    # Compter l'utilisation actuelle
    from apps.projects.models import Project
    from apps.investments.models import Investment

    projects_count = Project.objects.filter(owner=request.user).count()
    investments_count = Investment.objects.filter(investor=request.user).count()

    return Response({
        'plan': plan.name,
        'limits': {
            'projects': {
                'max': plan.max_projects,
                'used': projects_count,
                'remaining': max(0, plan.max_projects - projects_count) if plan.max_projects > 0 else None,
                'unlimited': plan.is_unlimited_projects,
            },
            'investments': {
                'max': plan.max_investments,
                'used': investments_count,
                'remaining': max(0, plan.max_investments - investments_count) if plan.max_investments > 0 else None,
                'unlimited': plan.is_unlimited_investments,
            },
            'messages': {
                'max': plan.max_messages,
                'unlimited': plan.is_unlimited_messages,
            },
        },
        'features': {
            'ai_matching': plan.ai_matching,
            'priority_support': plan.priority_support,
            'advanced_analytics': plan.advanced_analytics,
            'custom_branding': plan.custom_branding,
        },
        'subscription_status': subscription.get_status_display() if subscription else 'Aucun abonnement',
        'expires_at': subscription.expires_at.isoformat() if subscription else None,
        'days_remaining': subscription.days_remaining if subscription else 0,
    })
