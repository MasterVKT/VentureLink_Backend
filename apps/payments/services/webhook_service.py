"""
Service de traitement des webhooks My-CoolPay.

Ce service est responsable de :
- La validation de la signature HMAC des webhooks
- Le routage des événements vers les handlers appropriés
- La mise à jour des paiements, investissements et abonnements
- L'envoi des notifications aux utilisateurs concernés

Événements gérés :
    payment.success      → paiement complété
    payment.failed       → paiement échoué
    payment.refunded     → paiement remboursé
    subscription.created → abonnement créé
    subscription.renewed → abonnement renouvelé
    subscription.cancelled → abonnement annulé
"""
import logging
import hmac
import hashlib
from typing import Optional
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction

from apps.payments.models import Payment, Refund, UserSubscription

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service pour valider et traiter les webhooks My-CoolPay.
    """

    # ------------------------------------------------------------------
    # Vérification de signature
    # ------------------------------------------------------------------

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Vérifier la signature HMAC-SHA256 d'un webhook My-CoolPay.

        La signature est calculée sur le corps brut de la requête (string UTF-8)
        avec le secret webhook comme clé HMAC.

        Args:
            payload: Corps de la requête en string (avant parsing JSON).
            signature: Valeur du header de signature (X-MyCoolPay-Signature).
            secret: Secret webhook configuré dans les settings.

        Returns:
            True si la signature est valide, False sinon.
        """
        if not payload or not signature or not secret:
            logger.warning(
                "verify_signature: payload, signature ou secret manquant."
            )
            return False

        try:
            expected = hmac.new(
                key=secret.encode('utf-8'),
                msg=payload.encode('utf-8'),
                digestmod=hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(expected, signature.lower())

            if not is_valid:
                logger.warning(
                    f"Signature webhook invalide. "
                    f"Reçue: {signature[:20]}... "
                    f"Attendue: {expected[:20]}..."
                )
            return is_valid

        except Exception as exc:
            logger.exception(f"Erreur lors de la vérification de signature: {exc}")
            return False

    # ------------------------------------------------------------------
    # Routage des événements
    # ------------------------------------------------------------------

    @staticmethod
    def process_webhook_event(event_data: dict) -> bool:
        """
        Router un événement webhook vers le handler approprié.

        Args:
            event_data: Données JSON de l'événement.

        Returns:
            True si l'événement a été traité avec succès.
        """
        event_type = event_data.get('event_type')
        if not event_type:
            logger.error("Événement webhook reçu sans 'event_type'.")
            return False

        logger.info(f"Traitement webhook My-CoolPay: event_type={event_type}")

        handlers = {
            'payment.success': WebhookService._handle_payment_success,
            'payment.failed': WebhookService._handle_payment_failed,
            'payment.refunded': WebhookService._handle_payment_refunded,
            'subscription.created': WebhookService._handle_subscription_created,
            'subscription.renewed': WebhookService._handle_subscription_renewed,
            'subscription.cancelled': WebhookService._handle_subscription_cancelled,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(event_data)

        logger.warning(f"Type d'événement webhook non géré: {event_type}")
        return False

    # ------------------------------------------------------------------
    # Handlers — Paiements
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_payment_success(event_data: dict) -> bool:
        """
        Traiter un événement payment.success.

        Met à jour le paiement, l'investissement ou l'abonnement associé,
        puis envoie les notifications appropriées.
        """
        transaction_ref = event_data.get('transaction_ref')
        app_transaction_ref = event_data.get('app_transaction_ref')

        if not transaction_ref:
            logger.error("payment.success: 'transaction_ref' manquant.")
            return False

        try:
            # Retrouver le paiement (par référence externe ou interne)
            payment = WebhookService._find_payment(transaction_ref, app_transaction_ref)
            if not payment:
                return False

            with db_transaction.atomic():
                # Éviter le double traitement
                if payment.status == Payment.PaymentStatus.COMPLETED:
                    logger.info(f"Paiement {payment.id} déjà complété — ignoré.")
                    return True

                old_status = payment.status
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.completed_at = timezone.now()

                # Enrichir les métadonnées avec les détails du webhook
                payment.metadata.update({
                    'webhook_transaction_ref': transaction_ref,
                    'webhook_payment_method': event_data.get('payment_method', ''),
                    'webhook_transaction_date': event_data.get('transaction_date', ''),
                })
                payment.save()

                logger.info(
                    f"Paiement {payment.id} mis à jour: "
                    f"{old_status} → {payment.status}"
                )

                # Traitement post-paiement selon le type
                if payment.payment_type == Payment.PaymentType.INVESTMENT:
                    WebhookService._complete_investment(payment)

                elif payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
                    try:
                        from apps.payments.services.subscription_service import SubscriptionService
                        SubscriptionService.activate_subscription_from_payment(payment)
                    except ImportError:
                        # SubscriptionService non disponible — activation via mycoolpay_service
                        try:
                            from apps.payments.services.mycoolpay_service import MyCoolPayService
                            service = MyCoolPayService.__new__(MyCoolPayService)
                            service._activate_subscription(payment)
                        except Exception as sub_exc:
                            logger.warning(f"Activation abonnement non effectuée: {sub_exc}")

                # Notification de succès
                WebhookService._notify_payment_success(payment)

            return True

        except Exception as exc:
            logger.exception(f"Erreur lors du traitement payment.success: {exc}")
            return False

    @staticmethod
    def _handle_payment_failed(event_data: dict) -> bool:
        """
        Traiter un événement payment.failed.

        Met à jour le paiement et l'objet associé (investissement/abonnement),
        puis notifie l'utilisateur.
        """
        transaction_ref = event_data.get('transaction_ref')
        app_transaction_ref = event_data.get('app_transaction_ref')

        if not transaction_ref:
            logger.error("payment.failed: 'transaction_ref' manquant.")
            return False

        try:
            payment = WebhookService._find_payment(transaction_ref, app_transaction_ref)
            if not payment:
                return False

            with db_transaction.atomic():
                if payment.status == Payment.PaymentStatus.FAILED:
                    logger.info(f"Paiement {payment.id} déjà en échec — ignoré.")
                    return True

                old_status = payment.status
                payment.status = Payment.PaymentStatus.FAILED
                payment.metadata.update({
                    'webhook_error_code': event_data.get('error_code', ''),
                    'webhook_error_details': event_data.get('error_details', ''),
                    'webhook_failure_date': event_data.get('transaction_date', ''),
                })
                payment.save()

                logger.info(
                    f"Paiement {payment.id} mis à jour: "
                    f"{old_status} → {payment.status}"
                )

                # Mettre à jour l'investissement associé si applicable
                if payment.payment_type == Payment.PaymentType.INVESTMENT:
                    WebhookService._fail_investment(payment)

                # Notification d'échec
                WebhookService._notify_payment_failed(payment)

            return True

        except Exception as exc:
            logger.exception(f"Erreur lors du traitement payment.failed: {exc}")
            return False

    @staticmethod
    def _handle_payment_refunded(event_data: dict) -> bool:
        """
        Traiter un événement payment.refunded.

        Crée ou met à jour l'enregistrement de remboursement et notifie l'utilisateur.
        """
        transaction_ref = event_data.get('transaction_ref')
        refund_ref = event_data.get('refund_ref')
        refund_amount = event_data.get('refund_amount')

        if not transaction_ref or not refund_ref:
            logger.error("payment.refunded: 'transaction_ref' ou 'refund_ref' manquant.")
            return False

        try:
            payment = Payment.objects.filter(
                external_payment_id=transaction_ref
            ).first()

            if not payment:
                logger.error(
                    f"payment.refunded: paiement introuvable pour ref={transaction_ref}"
                )
                return False

            with db_transaction.atomic():
                # Vérifier si le remboursement existe déjà
                existing = Refund.objects.filter(external_refund_id=refund_ref).first()
                if existing:
                    existing.status = Refund.RefundStatus.COMPLETED
                    existing.completed_at = timezone.now()
                    existing.save()
                    logger.info(f"Remboursement {existing.id} marqué complété.")
                    return True

                # Créer le remboursement
                amount = float(refund_amount) if refund_amount else float(payment.amount)

                refund = Refund.objects.create(
                    payment=payment,
                    amount=amount,
                    currency=payment.currency,
                    status=Refund.RefundStatus.COMPLETED,
                    external_refund_id=refund_ref,
                    reason=event_data.get('refund_reason', ''),
                    completed_at=timezone.now(),
                )

                # Mettre à jour le statut du paiement
                if amount >= float(payment.amount):
                    payment.status = Payment.PaymentStatus.REFUNDED
                else:
                    payment.status = Payment.PaymentStatus.PARTIALLY_REFUNDED
                payment.save()

                logger.info(
                    f"Remboursement créé: payment={payment.id} "
                    f"montant={amount} {payment.currency}"
                )

                # Notification
                WebhookService._notify_refund(payment, refund)

            return True

        except Exception as exc:
            logger.exception(f"Erreur lors du traitement payment.refunded: {exc}")
            return False

    # ------------------------------------------------------------------
    # Handlers — Abonnements
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_subscription_created(event_data: dict) -> bool:
        """Traiter un événement subscription.created."""
        try:
            from apps.payments.services.subscription_service import SubscriptionService
            return SubscriptionService.handle_subscription_created_webhook(event_data)
        except ImportError:
            logger.warning("SubscriptionService non disponible pour subscription.created.")
            return False
        except Exception as exc:
            logger.exception(f"Erreur subscription.created: {exc}")
            return False

    @staticmethod
    def _handle_subscription_renewed(event_data: dict) -> bool:
        """
        Traiter un événement subscription.renewed.

        Prolonge la période de l'abonnement actif de l'utilisateur.
        """
        mycoolpay_subscription_id = event_data.get('subscription_id')
        app_transaction_ref = event_data.get('app_transaction_ref')

        try:
            # Retrouver l'abonnement
            subscription = None

            if mycoolpay_subscription_id:
                subscription = UserSubscription.objects.filter(
                    mycoolpay_subscription_id=mycoolpay_subscription_id
                ).first()

            if not subscription and app_transaction_ref:
                # Chercher via le paiement associé
                payment = Payment.objects.filter(id=app_transaction_ref).first()
                if payment:
                    subscription = UserSubscription.objects.filter(
                        user=payment.user,
                        status=UserSubscription.SubscriptionStatus.ACTIVE,
                    ).first()

            if not subscription:
                logger.error(
                    f"subscription.renewed: abonnement introuvable "
                    f"(subscription_id={mycoolpay_subscription_id})"
                )
                return False

            with db_transaction.atomic():
                plan = subscription.plan
                new_end = subscription.expires_at + timezone.timedelta(
                    days=plan.duration_days
                )
                subscription.expires_at = new_end
                subscription.status = UserSubscription.SubscriptionStatus.ACTIVE
                subscription.last_payment_date = timezone.now()
                subscription.save()

                logger.info(
                    f"Abonnement {subscription.id} renouvelé jusqu'au {new_end.date()}"
                )

                # Notification
                try:
                    from apps.notifications.services.notification_service import NotificationService
                    NotificationService.create_from_template(
                        template_code='subscription_renewed',
                        recipient=subscription.user,
                        context_data={
                            'plan_name': plan.name,
                            'end_date': new_end.strftime('%d/%m/%Y'),
                        },
                    )
                except Exception as notif_exc:
                    logger.warning(f"Notification renouvellement non envoyée: {notif_exc}")

            return True

        except Exception as exc:
            logger.exception(f"Erreur subscription.renewed: {exc}")
            return False

    @staticmethod
    def _handle_subscription_cancelled(event_data: dict) -> bool:
        """
        Traiter un événement subscription.cancelled.

        Annule l'abonnement actif de l'utilisateur.
        """
        mycoolpay_subscription_id = event_data.get('subscription_id')

        try:
            from apps.payments.services.subscription_service import SubscriptionService
            return SubscriptionService.handle_subscription_cancelled_webhook(event_data)
        except ImportError:
            pass
        except Exception as exc:
            logger.exception(f"Erreur subscription.cancelled via SubscriptionService: {exc}")

        # Fallback direct
        try:
            if not mycoolpay_subscription_id:
                logger.error("subscription.cancelled: 'subscription_id' manquant.")
                return False

            subscription = UserSubscription.objects.filter(
                mycoolpay_subscription_id=mycoolpay_subscription_id,
                status__in=[
                    UserSubscription.SubscriptionStatus.ACTIVE,
                    UserSubscription.SubscriptionStatus.TRIAL,
                ],
            ).first()

            if not subscription:
                logger.warning(
                    f"subscription.cancelled: abonnement actif introuvable "
                    f"(subscription_id={mycoolpay_subscription_id})"
                )
                return False

            with db_transaction.atomic():
                subscription.status = UserSubscription.SubscriptionStatus.CANCELLED
                subscription.cancelled_at = timezone.now()
                subscription.save()

                logger.info(f"Abonnement {subscription.id} annulé via webhook.")

                try:
                    from apps.notifications.services.notification_service import NotificationService
                    NotificationService.create_from_template(
                        template_code='subscription_cancelled',
                        recipient=subscription.user,
                        context_data={'plan_name': subscription.plan.name},
                    )
                except Exception as notif_exc:
                    logger.warning(f"Notification annulation non envoyée: {notif_exc}")

            return True

        except Exception as exc:
            logger.exception(f"Erreur subscription.cancelled: {exc}")
            return False

    # ------------------------------------------------------------------
    # Helpers — Investissements
    # ------------------------------------------------------------------

    @staticmethod
    def _complete_investment(payment: 'Payment') -> None:
        """
        Finaliser un investissement après paiement réussi.

        Met à jour le statut de l'investissement et le montant levé du projet,
        puis envoie les notifications à l'investisseur et au porteur de projet.
        """
        try:
            from apps.investments.models import Investment
            from django.contrib.contenttypes.models import ContentType

            # Retrouver l'investissement lié au paiement (via GenericForeignKey)
            investment = None

            if payment.content_type and payment.object_id:
                ct = ContentType.objects.get_for_model(Investment)
                if payment.content_type == ct:
                    try:
                        investment = Investment.objects.select_related(
                            'project', 'investor'
                        ).get(id=payment.object_id)
                    except Investment.DoesNotExist:
                        pass

            # Fallback : chercher via les métadonnées
            if not investment:
                investment_id = payment.metadata.get('investment_id')
                if investment_id:
                    try:
                        investment = Investment.objects.select_related(
                            'project', 'investor'
                        ).get(id=investment_id)
                    except Investment.DoesNotExist:
                        pass

            if not investment:
                logger.warning(
                    f"Investissement introuvable pour le paiement {payment.id}. "
                    f"Vérifiez content_type/object_id ou metadata['investment_id']."
                )
                return

            # Mettre à jour l'investissement
            investment.status = Investment.STATUS_COMPLETED
            investment.completed_at = timezone.now()
            investment.save(update_fields=['status', 'completed_at'])

            # Mettre à jour le projet si le financement est atteint
            project = investment.project

            logger.info(
                f"Investissement {investment.id} complété: "
                f"projet={project.title} montant={investment.amount} {investment.currency}"
            )

            # Notifications
            WebhookService._notify_investment_success(payment, investment, project)

        except Exception as exc:
            logger.exception(
                f"Erreur lors de la finalisation de l'investissement "
                f"(paiement {payment.id}): {exc}"
            )

    @staticmethod
    def _fail_investment(payment: 'Payment') -> None:
        """
        Marquer un investissement comme échoué après un paiement raté.
        """
        try:
            from apps.investments.models import Investment
            from django.contrib.contenttypes.models import ContentType

            investment = None

            if payment.content_type and payment.object_id:
                ct = ContentType.objects.get_for_model(Investment)
                if payment.content_type == ct:
                    try:
                        investment = Investment.objects.get(id=payment.object_id)
                    except Investment.DoesNotExist:
                        pass

            if not investment:
                investment_id = payment.metadata.get('investment_id')
                if investment_id:
                    try:
                        investment = Investment.objects.get(id=investment_id)
                    except Investment.DoesNotExist:
                        pass

            if not investment:
                return

            investment.status = Investment.STATUS_CANCELLED
            investment.save(update_fields=['status'])

            logger.info(f"Investissement {investment.id} annulé suite à l'échec du paiement.")

        except Exception as exc:
            logger.exception(
                f"Erreur lors de l'annulation de l'investissement "
                f"(paiement {payment.id}): {exc}"
            )

    # ------------------------------------------------------------------
    # Helpers — Notifications
    # ------------------------------------------------------------------

    @staticmethod
    def _notify_payment_success(payment: 'Payment') -> None:
        """Envoyer une notification de paiement réussi."""
        if not payment.user:
            return
        try:
            from apps.notifications.services.notification_service import NotificationService
            from apps.notifications.models import NotificationCategory

            NotificationService.create_notification(
                recipient=payment.user,
                title="Paiement confirmé ✓",
                content=(
                    f"Votre paiement de {payment.amount} {payment.currency} "
                    f"a été confirmé avec succès."
                ),
                category=NotificationCategory.PAYMENT,
                related_object=payment,
            )
        except Exception as exc:
            logger.warning(f"Notification paiement succès non envoyée: {exc}")

    @staticmethod
    def _notify_payment_failed(payment: 'Payment') -> None:
        """Envoyer une notification d'échec de paiement."""
        if not payment.user:
            return
        try:
            from apps.notifications.services.notification_service import NotificationService
            from apps.notifications.models import NotificationCategory

            NotificationService.create_notification(
                recipient=payment.user,
                title="Paiement échoué",
                content=(
                    f"Votre paiement de {payment.amount} {payment.currency} "
                    f"a échoué. Veuillez réessayer ou contacter le support."
                ),
                category=NotificationCategory.PAYMENT,
                related_object=payment,
            )
        except Exception as exc:
            logger.warning(f"Notification paiement échec non envoyée: {exc}")

    @staticmethod
    def _notify_refund(payment: 'Payment', refund: 'Refund') -> None:
        """Envoyer une notification de remboursement."""
        if not payment.user:
            return
        try:
            from apps.notifications.services.notification_service import NotificationService
            from apps.notifications.models import NotificationCategory

            NotificationService.create_notification(
                recipient=payment.user,
                title="Remboursement effectué",
                content=(
                    f"Un remboursement de {refund.amount} {refund.currency} "
                    f"a été initié sur votre compte."
                ),
                category=NotificationCategory.PAYMENT,
                related_object=payment,
            )
        except Exception as exc:
            logger.warning(f"Notification remboursement non envoyée: {exc}")

    @staticmethod
    def _notify_investment_success(
        payment: 'Payment',
        investment,
        project,
    ) -> None:
        """
        Envoyer les notifications de succès d'investissement :
        - à l'investisseur
        - au porteur de projet
        """
        try:
            from apps.notifications.services.notification_service import NotificationService
            from apps.notifications.models import NotificationCategory

            # Notification à l'investisseur
            NotificationService.create_notification(
                recipient=payment.user,
                title="Investissement confirmé ✓",
                content=(
                    f"Votre investissement de {investment.amount} {investment.currency} "
                    f"dans le projet « {project.title} » a été confirmé."
                ),
                category=NotificationCategory.INVESTMENT,
                related_object=investment,
            )

            # Notification au porteur de projet
            if hasattr(project, 'creator') and project.creator:
                investor_name = (
                    payment.user.get_full_name() or payment.user.email
                )
                NotificationService.create_notification(
                    recipient=project.creator,
                    title="Nouvel investissement reçu 🎉",
                    content=(
                        f"{investor_name} vient d'investir "
                        f"{investment.amount} {investment.currency} "
                        f"dans votre projet « {project.title} »."
                    ),
                    category=NotificationCategory.INVESTMENT,
                    related_object=investment,
                )

        except Exception as exc:
            logger.warning(f"Notifications investissement non envoyées: {exc}")

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    @staticmethod
    def _find_payment(
        transaction_ref: str,
        app_transaction_ref: Optional[str] = None,
    ) -> Optional['Payment']:
        """
        Retrouver un paiement par référence externe ou interne.

        Args:
            transaction_ref: Référence My-CoolPay.
            app_transaction_ref: ID interne VentureLink (UUID).

        Returns:
            Instance Payment ou None.
        """
        # Chercher d'abord par référence externe
        payment = Payment.objects.filter(
            external_payment_id=transaction_ref
        ).first()

        # Fallback sur l'ID interne
        if not payment and app_transaction_ref:
            try:
                payment = Payment.objects.get(id=app_transaction_ref)
            except (Payment.DoesNotExist, Exception):
                pass

        if not payment:
            logger.error(
                f"Paiement introuvable: "
                f"transaction_ref={transaction_ref} "
                f"app_transaction_ref={app_transaction_ref}"
            )

        return payment
