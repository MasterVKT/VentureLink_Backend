"""
Service d'intégration My-CoolPay pour VentureLink.

Ce service gère toutes les interactions avec l'API My-CoolPay :
- Création de paylinks (liens de paiement)
- Initiation de paiements directs (payin)
- Autorisation OTP
- Vérification de statut de transaction
- Vérification de signature HMAC pour les callbacks/webhooks
- Paiements d'abonnements
- Remboursements (payout)

Documentation My-CoolPay : https://my-coolpay.com/docs
"""
import requests
import json
import logging
import hashlib
import hmac
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone

from apps.payments.models import (
    Payment,
    PaymentMethod,
    SubscriptionPlan,
    UserSubscription,
)

logger = logging.getLogger(__name__)


class MyCoolPayError(Exception):
    """Exception levée pour les erreurs liées à l'API My-CoolPay."""
    pass


class MyCoolPayService:
    """
    Service d'intégration My-CoolPay.

    Utilise l'API My-CoolPay pour initier et vérifier des paiements,
    gérer les abonnements et traiter les callbacks/webhooks.

    Usage:
        service = MyCoolPayService()          # sandbox par défaut (DEBUG=True)
        service = MyCoolPayService(sandbox=False)  # production
        # ou via le helper :
        service = get_mycoolpay_service()
    """

    # URL de base de l'API My-CoolPay
    API_BASE_URL = "https://my-coolpay.com/api"

    # Devises supportées
    SUPPORTED_CURRENCIES = ['XAF', 'EUR', 'USD', 'XOF']

    # Opérateurs de paiement mobile supportés
    MOBILE_OPERATORS = {
        'CM_OM': 'Orange Money Cameroun',
        'CM_MOMO': 'MTN Mobile Money Cameroun',
        'SN_OM': 'Orange Money Sénégal',
        'CI_OM': "Orange Money Côte d'Ivoire",
        'EU_CARD': 'Carte bancaire européenne',
    }

    def __init__(self, sandbox: bool = True):
        """
        Initialiser le service My-CoolPay.

        Args:
            sandbox: True pour utiliser l'environnement sandbox, False pour la production.
        """
        self.sandbox = sandbox

        if sandbox:
            self.public_key = getattr(settings, 'MYCOOLPAY_SANDBOX_PUBLIC_KEY', '')
            self.private_key = getattr(settings, 'MYCOOLPAY_SANDBOX_PRIVATE_KEY', '')
            self.webhook_secret = getattr(settings, 'MYCOOLPAY_SANDBOX_WEBHOOK_SECRET', '')
        else:
            self.public_key = getattr(settings, 'MYCOOLPAY_PUBLIC_KEY', '')
            self.private_key = getattr(settings, 'MYCOOLPAY_PRIVATE_KEY', '')
            self.webhook_secret = getattr(settings, 'MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET', '')

        if not self.public_key:
            raise MyCoolPayError(
                "Clé publique My-CoolPay manquante dans les settings. "
                "Vérifiez MYCOOLPAY_SANDBOX_PUBLIC_KEY ou MYCOOLPAY_PUBLIC_KEY."
            )

    # ------------------------------------------------------------------
    # Méthodes internes
    # ------------------------------------------------------------------

    def _get_headers(self) -> Dict[str, str]:
        """Retourner les headers HTTP communs pour les requêtes API."""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _make_request(
        self,
        endpoint: str,
        method: str = 'POST',
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Effectuer une requête HTTP vers l'API My-CoolPay.

        Args:
            endpoint: Chemin de l'endpoint (ex: 'paylink', 'payin', 'status/REF').
            method: Méthode HTTP ('GET', 'POST').
            data: Corps de la requête (pour POST).

        Returns:
            Réponse JSON de l'API.

        Raises:
            MyCoolPayError: En cas d'erreur HTTP ou de connexion.
        """
        # Construction de l'URL selon le format My-CoolPay
        if endpoint == 'paylink':
            url = f"{self.API_BASE_URL}/{self.public_key}/paylink"
        elif endpoint == 'payin':
            url = f"{self.API_BASE_URL}/{self.public_key}/payin"
        elif endpoint == 'authorize':
            url = f"{self.API_BASE_URL}/{self.public_key}/authorize"
        elif endpoint == 'payout':
            url = f"{self.API_BASE_URL}/{self.public_key}/payout"
        elif endpoint == 'balance':
            url = f"{self.API_BASE_URL}/{self.public_key}/balance"
        elif endpoint.startswith('status/'):
            ref = endpoint.split('/', 1)[1]
            url = f"{self.API_BASE_URL}/{self.public_key}/status/{ref}"
        else:
            url = f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"

        try:
            logger.info(f"My-CoolPay {method.upper()} {url}")

            if method.upper() == 'GET':
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    params=data,
                    timeout=30,
                )
            else:
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    json=data,
                    timeout=30,
                )

            logger.info(f"My-CoolPay réponse: HTTP {response.status_code}")

            if response.status_code >= 400:
                error_msg = f"Erreur API My-CoolPay: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" — {error_data.get('message', response.text)}"
                except Exception:
                    error_msg += f" — {response.text}"
                logger.error(error_msg)
                raise MyCoolPayError(error_msg)

            return response.json()

        except requests.exceptions.Timeout:
            msg = f"Timeout lors de la connexion à My-CoolPay ({url})"
            logger.error(msg)
            raise MyCoolPayError(msg)

        except requests.exceptions.ConnectionError as exc:
            msg = f"Erreur de connexion à My-CoolPay: {exc}"
            logger.error(msg)
            raise MyCoolPayError(msg)

        except requests.exceptions.RequestException as exc:
            msg = f"Erreur réseau My-CoolPay: {exc}"
            logger.error(msg)
            raise MyCoolPayError(msg)

    # ------------------------------------------------------------------
    # Paiements — Paylink
    # ------------------------------------------------------------------

    def create_paylink(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Créer un lien de paiement My-CoolPay (paylink).

        Le frontend redirige l'utilisateur vers l'URL retournée pour qu'il
        choisisse son opérateur et finalise le paiement.

        Champs requis dans payment_data:
            - transaction_amount (int)
            - transaction_currency (str) : XAF, EUR, USD, XOF
            - transaction_reason (str)
            - app_transaction_ref (str) : référence unique côté VentureLink
            - customer_phone_number (str) : format international (+237...)
            - customer_name (str)
            - customer_email (str)

        Champs optionnels:
            - customer_lang (str, défaut 'fr')
            - return_url (str)
            - cancel_url (str)
            - callback_url (str)

        Returns:
            Dict avec 'payment_url' et 'transaction_ref'.
        """
        required_fields = [
            'transaction_amount',
            'transaction_currency',
            'transaction_reason',
            'app_transaction_ref',
            'customer_phone_number',
            'customer_name',
            'customer_email',
        ]
        for field in required_fields:
            if field not in payment_data:
                raise MyCoolPayError(f"Champ requis manquant pour paylink: {field}")

        currency = payment_data['transaction_currency']
        if currency not in self.SUPPORTED_CURRENCIES:
            raise MyCoolPayError(
                f"Devise non supportée: {currency}. "
                f"Devises acceptées: {', '.join(self.SUPPORTED_CURRENCIES)}"
            )

        # Valeurs par défaut
        data = {
            'customer_lang': 'fr',
            'return_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/payments/success/',
            'cancel_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/payments/cancel/',
            'callback_url': getattr(settings, 'SITE_URL', 'http://localhost:8000') + '/api/v1/payments/mycoolpay/callback/',
            **payment_data,
        }

        logger.info(
            f"Création paylink: ref={data['app_transaction_ref']} "
            f"montant={data['transaction_amount']} {data['transaction_currency']}"
        )
        return self._make_request('paylink', 'POST', data)

    # ------------------------------------------------------------------
    # Paiements — Payin direct
    # ------------------------------------------------------------------

    def initiate_payin(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initier un paiement direct (payin) avec un opérateur spécifique.

        Champs requis supplémentaires par rapport à create_paylink:
            - transaction_operator (str) : CM_OM, CM_MOMO, EU_CARD, etc.

        Returns:
            Dict avec 'action' (REQUIRE_OTP, PENDING, etc.) et 'transaction_ref'.
        """
        required_fields = [
            'transaction_amount',
            'transaction_currency',
            'transaction_reason',
            'app_transaction_ref',
            'customer_phone_number',
            'customer_name',
            'customer_email',
            'transaction_operator',
        ]
        for field in required_fields:
            if field not in payment_data:
                raise MyCoolPayError(f"Champ requis manquant pour payin: {field}")

        operator = payment_data['transaction_operator']
        if operator not in self.MOBILE_OPERATORS:
            raise MyCoolPayError(
                f"Opérateur non supporté: {operator}. "
                f"Opérateurs acceptés: {', '.join(self.MOBILE_OPERATORS.keys())}"
            )

        logger.info(
            f"Initiation payin: ref={payment_data['app_transaction_ref']} "
            f"opérateur={operator}"
        )
        return self._make_request('payin', 'POST', payment_data)

    def authorize_payin(self, transaction_ref: str, otp_code: str) -> Dict[str, Any]:
        """
        Autoriser un paiement payin avec le code OTP reçu par SMS.

        Args:
            transaction_ref: Référence de transaction retournée par initiate_payin.
            otp_code: Code OTP reçu par l'utilisateur.

        Returns:
            Réponse d'autorisation My-CoolPay.
        """
        data = {
            'transaction_ref': transaction_ref,
            'code': otp_code,
        }
        logger.info(f"Autorisation OTP pour transaction: {transaction_ref}")
        return self._make_request('authorize', 'POST', data)

    # ------------------------------------------------------------------
    # Remboursements — Payout
    # ------------------------------------------------------------------

    def initiate_payout(self, payout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initier un remboursement (payout) vers un numéro mobile.

        Champs requis:
            - transaction_amount, transaction_currency, transaction_reason
            - transaction_operator, app_transaction_ref
            - customer_phone_number, customer_name, customer_email

        Returns:
            Réponse My-CoolPay du payout.
        """
        required_fields = [
            'transaction_amount',
            'transaction_currency',
            'transaction_reason',
            'transaction_operator',
            'app_transaction_ref',
            'customer_phone_number',
            'customer_name',
            'customer_email',
        ]
        for field in required_fields:
            if field not in payout_data:
                raise MyCoolPayError(f"Champ requis manquant pour payout: {field}")

        logger.info(
            f"Initiation payout: ref={payout_data['app_transaction_ref']} "
            f"montant={payout_data['transaction_amount']} {payout_data['transaction_currency']}"
        )
        return self._make_request('payout', 'POST', payout_data)

    # ------------------------------------------------------------------
    # Vérification de statut
    # ------------------------------------------------------------------

    def check_transaction_status(self, transaction_ref: str) -> Dict[str, Any]:
        """
        Vérifier le statut d'une transaction My-CoolPay.

        Args:
            transaction_ref: Référence de transaction My-CoolPay.

        Returns:
            Dict avec 'transaction_status' (PENDING, SUCCESS, CANCELED, FAILED).
        """
        logger.info(f"Vérification statut transaction: {transaction_ref}")
        return self._make_request(f'status/{transaction_ref}', 'GET')

    def get_balance(self) -> Dict[str, Any]:
        """
        Obtenir le solde du compte My-CoolPay.

        Returns:
            Dict avec les informations de solde.
        """
        return self._make_request('balance', 'GET')

    # ------------------------------------------------------------------
    # Sécurité — Vérification de signature HMAC
    # ------------------------------------------------------------------

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Vérifier la signature HMAC-SHA256 d'un webhook My-CoolPay.

        My-CoolPay envoie la signature dans le header X-MyCoolPay-Signature
        (ou X-MCP-Signature selon la version). La signature est calculée avec
        HMAC-SHA256 sur le corps brut de la requête.

        Args:
            payload: Corps brut de la requête (bytes).
            signature: Valeur du header de signature.

        Returns:
            True si la signature est valide, False sinon.
        """
        if not self.webhook_secret:
            logger.warning(
                "Webhook secret non configuré — vérification de signature ignorée. "
                "Configurez MYCOOLPAY_SANDBOX_WEBHOOK_SECRET ou MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET."
            )
            return False

        if not payload or not signature:
            logger.warning("Payload ou signature manquant pour la vérification HMAC.")
            return False

        try:
            expected = hmac.new(
                key=self.webhook_secret.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha256,
            ).hexdigest()

            # Comparaison résistante aux timing attacks
            is_valid = hmac.compare_digest(expected, signature.lower())

            if not is_valid:
                logger.warning(
                    f"Signature webhook invalide. "
                    f"Reçue: {signature[:20]}... "
                    f"Attendue: {expected[:20]}..."
                )
            return is_valid

        except Exception as exc:
            logger.exception(f"Erreur lors de la vérification de signature HMAC: {exc}")
            return False

    def verify_callback_signature(self, callback_data: Dict[str, Any]) -> bool:
        """
        Vérifier la signature d'un callback My-CoolPay (format query-string signé).

        La signature est calculée sur les paramètres triés par clé, joints par '&'.

        Args:
            callback_data: Données du callback (la clé 'signature' sera extraite).

        Returns:
            True si la signature est valide.
        """
        if not self.private_key:
            logger.warning("Clé privée My-CoolPay non configurée — vérification ignorée.")
            return False

        data = dict(callback_data)
        signature = data.pop('signature', None)

        if not signature:
            logger.warning("Signature absente dans les données de callback.")
            return False

        try:
            sorted_items = sorted(data.items())
            data_string = '&'.join(f"{k}={v}" for k, v in sorted_items)

            expected = hmac.new(
                key=self.private_key.encode('utf-8'),
                msg=data_string.encode('utf-8'),
                digestmod=hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected, signature)

        except Exception as exc:
            logger.exception(f"Erreur lors de la vérification de signature callback: {exc}")
            return False

    def verify_callback_ip(self, ip_address: str) -> bool:
        """
        Vérifier si une adresse IP est autorisée pour les callbacks My-CoolPay.

        Les IPs autorisées sont configurées dans MYCOOLPAY_ALLOWED_IPS.
        En mode DEBUG, toutes les IPs sont acceptées.

        Args:
            ip_address: Adresse IP à vérifier.

        Returns:
            True si l'IP est autorisée.
        """
        if getattr(settings, 'DEBUG', False):
            return True

        allowed_ips = getattr(settings, 'MYCOOLPAY_ALLOWED_IPS', [])
        if not allowed_ips:
            # Si aucune IP configurée, accepter (à configurer en production)
            logger.warning("MYCOOLPAY_ALLOWED_IPS non configuré — toutes les IPs acceptées.")
            return True

        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)

            for allowed in allowed_ips:
                try:
                    if '/' in allowed:
                        if ip in ipaddress.ip_network(allowed, strict=False):
                            return True
                    else:
                        if ip == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    continue

            logger.warning(f"IP non autorisée pour callback My-CoolPay: {ip_address}")
            return False

        except ValueError:
            logger.warning(f"Adresse IP invalide: {ip_address}")
            return False

    # ------------------------------------------------------------------
    # Paiements d'abonnement
    # ------------------------------------------------------------------

    def process_subscription_payment(
        self,
        user,
        subscription_plan: 'SubscriptionPlan',
        phone_number: str,
        currency: str = 'XAF',
    ) -> Tuple[bool, str, Dict]:
        """
        Créer un paylink pour le paiement d'un abonnement.

        Args:
            user: Instance utilisateur Django.
            subscription_plan: Plan d'abonnement à souscrire.
            phone_number: Numéro de téléphone de l'utilisateur (format international).
            currency: Devise du paiement (XAF, EUR, USD).

        Returns:
            Tuple (success: bool, message: str, data: dict).
            data contient 'payment_id', 'payment_url', 'transaction_ref' en cas de succès.
        """
        try:
            # Obtenir le prix dans la devise demandée
            amount = subscription_plan.get_price_for_currency(currency)

            # Normaliser le numéro de téléphone
            phone = phone_number.strip()
            if not phone:
                return False, "Numéro de téléphone manquant.", {}

            digits = phone.replace('+', '').replace(' ', '').replace('-', '')
            if len(digits) < 9:
                return False, "Numéro de téléphone invalide (minimum 9 chiffres).", {}

            if not phone.startswith('+'):
                phone = f'+237{phone}'

            # Créer l'enregistrement de paiement en base
            payment = Payment.objects.create(
                user=user,
                amount=amount,
                currency=currency,
                payment_type=Payment.PaymentType.SUBSCRIPTION,
                description=f"Abonnement {subscription_plan.name}",
                status=Payment.PaymentStatus.PENDING,
                is_test=self.sandbox,
                metadata={
                    'subscription_plan_id': str(subscription_plan.id),
                    'plan_name': subscription_plan.name,
                    'duration_days': subscription_plan.duration_days,
                    'payment_method': 'MYCOOLPAY',
                    'phone_number': phone,
                },
            )

            # Préparer les données pour My-CoolPay
            payment_data = {
                'transaction_amount': int(amount),
                'transaction_currency': currency,
                'transaction_reason': f"Abonnement VentureLink — {subscription_plan.name}",
                'app_transaction_ref': str(payment.id),
                'customer_phone_number': phone,
                'customer_name': user.get_full_name() or user.email,
                'customer_email': user.email,
                'customer_lang': 'fr',
            }

            # Créer le paylink
            response = self.create_paylink(payment_data)

            # Mettre à jour le paiement avec la référence My-CoolPay
            payment.external_payment_id = response.get('transaction_ref', '')
            payment.external_checkout_url = response.get('payment_url', '')
            payment.save(update_fields=['external_payment_id', 'external_checkout_url'])

            logger.info(
                f"Paylink abonnement créé: user={user.id} "
                f"plan={subscription_plan.name} ref={payment.external_payment_id}"
            )

            return True, "Lien de paiement créé avec succès.", {
                'payment_id': str(payment.id),
                'payment_url': payment.external_checkout_url,
                'transaction_ref': payment.external_payment_id,
            }

        except MyCoolPayError as exc:
            logger.error(f"Erreur My-CoolPay lors du paiement abonnement: {exc}")
            return False, str(exc), {}

        except Exception as exc:
            logger.exception(f"Erreur inattendue lors du paiement abonnement: {exc}")
            return False, "Erreur interne lors de la création du paiement.", {}

    # ------------------------------------------------------------------
    # Traitement des callbacks
    # ------------------------------------------------------------------

    def handle_payment_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        Traiter un callback de paiement My-CoolPay.

        Vérifie la signature, met à jour le statut du paiement en base
        et active l'abonnement si applicable.

        Args:
            callback_data: Données JSON du callback.

        Returns:
            True si le callback a été traité avec succès.
        """
        try:
            # Vérifier la signature
            if not self.verify_callback_signature(dict(callback_data)):
                logger.warning("Signature de callback invalide — callback ignoré.")
                return False

            transaction_ref = callback_data.get('transaction_ref')
            app_transaction_ref = callback_data.get('app_transaction_ref')
            api_status = callback_data.get('transaction_status')

            if not all([transaction_ref, app_transaction_ref, api_status]):
                logger.warning(f"Données de callback incomplètes: {callback_data}")
                return False

            # Retrouver le paiement
            try:
                payment = Payment.objects.get(id=app_transaction_ref)
            except Payment.DoesNotExist:
                logger.warning(f"Paiement introuvable pour callback: {app_transaction_ref}")
                return False

            # Mettre à jour le statut
            status_map = {
                'SUCCESS': Payment.PaymentStatus.COMPLETED,
                'FAILED': Payment.PaymentStatus.FAILED,
                'CANCELED': Payment.PaymentStatus.CANCELLED,
            }
            new_status = status_map.get(api_status.upper())

            if new_status:
                payment.status = new_status
                if new_status == Payment.PaymentStatus.COMPLETED:
                    payment.completed_at = timezone.now()
                    # Activer l'abonnement si c'est un paiement d'abonnement
                    if payment.payment_type == Payment.PaymentType.SUBSCRIPTION:
                        self._activate_subscription(payment)

            payment.external_payment_id = transaction_ref
            payment.save()

            logger.info(
                f"Callback traité: payment={payment.id} "
                f"statut={api_status} → {new_status}"
            )
            return True

        except Exception as exc:
            logger.exception(f"Erreur lors du traitement du callback: {exc}")
            return False

    def _activate_subscription(self, payment: 'Payment') -> None:
        """
        Activer un abonnement après un paiement réussi.

        Args:
            payment: Paiement complété de type SUBSCRIPTION.
        """
        try:
            plan_id = payment.metadata.get('subscription_plan_id')
            if not plan_id:
                logger.error(f"subscription_plan_id manquant dans metadata du paiement {payment.id}")
                return

            plan = SubscriptionPlan.objects.get(id=plan_id)

            # Désactiver les abonnements actifs existants
            UserSubscription.objects.filter(
                user=payment.user,
                status__in=[
                    UserSubscription.SubscriptionStatus.ACTIVE,
                    UserSubscription.SubscriptionStatus.TRIAL,
                ],
            ).update(
                status=UserSubscription.SubscriptionStatus.CANCELLED,
                cancelled_at=timezone.now(),
            )

            # Créer le nouvel abonnement
            start = timezone.now()
            end = start + timezone.timedelta(days=plan.duration_days)

            subscription = UserSubscription.objects.create(
                user=payment.user,
                plan=plan,
                status=UserSubscription.SubscriptionStatus.ACTIVE,
                started_at=start,
                expires_at=end,
                billing_currency=payment.currency,
                last_payment_date=start,
                last_payment_amount=payment.amount,
            )

            logger.info(
                f"Abonnement activé: user={payment.user.id} "
                f"plan={plan.name} expire={end.date()}"
            )

            # Notification à l'utilisateur
            try:
                from apps.notifications.services.notification_service import NotificationService
                NotificationService.create_from_template(
                    template_code='subscription_activated',
                    recipient=payment.user,
                    context_data={
                        'plan_name': plan.name,
                        'end_date': end.strftime('%d/%m/%Y'),
                    },
                )
            except Exception as notif_exc:
                logger.warning(f"Notification abonnement non envoyée: {notif_exc}")

        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan d'abonnement introuvable: {plan_id}")
        except Exception as exc:
            logger.exception(f"Erreur lors de l'activation de l'abonnement: {exc}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_mycoolpay_service() -> MyCoolPayService:
    """
    Retourner une instance configurée du service My-CoolPay.

    Utilise le mode sandbox si DEBUG=True ou PAYMENT_SANDBOX_MODE=True.

    Returns:
        Instance de MyCoolPayService.
    """
    sandbox = getattr(settings, 'DEBUG', True) or getattr(settings, 'PAYMENT_SANDBOX_MODE', True)
    return MyCoolPayService(sandbox=bool(sandbox))
