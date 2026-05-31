"""
Service de sécurité pour les paiements.
Sprint 3 - B3.6 : Logs et Sécurité

Responsabilités :
- Audit trail de toutes les opérations sensibles
- Validation des montants et devises
- Détection des tentatives suspectes (rate limiting logique)
- Vérification de la cohérence des données de paiement
"""
import logging
import hashlib
import hmac
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('payments.security')

# ---------------------------------------------------------------------------
# Constantes de sécurité
# ---------------------------------------------------------------------------

# Montants limites (en XAF)
MIN_PAYMENT_AMOUNT_XAF = Decimal('100')       # 100 XAF minimum
MAX_PAYMENT_AMOUNT_XAF = Decimal('10000000')  # 10 millions XAF maximum

# Devises acceptées
ACCEPTED_CURRENCIES = {'XAF', 'EUR', 'USD'}

# Rate limiting : nombre max de tentatives de paiement par utilisateur par heure
MAX_PAYMENT_ATTEMPTS_PER_HOUR = 10

# Rate limiting : nombre max de souscriptions par utilisateur par jour
MAX_SUBSCRIPTION_ATTEMPTS_PER_DAY = 5

# Taux de conversion approximatifs vers XAF (pour validation des limites)
CURRENCY_TO_XAF = {
    'XAF': Decimal('1'),
    'EUR': Decimal('655.957'),
    'USD': Decimal('600'),
}


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

class PaymentAuditLogger:
    """
    Enregistre toutes les opérations sensibles liées aux paiements.
    Utilise un logger dédié 'payments.security' pour faciliter la centralisation
    des logs (Sentry, ELK, etc.).
    """

    @staticmethod
    def log_payment_initiated(user, amount, currency, reference, ip_address=None):
        """Journaliser l'initiation d'un paiement."""
        logger.info(
            "PAYMENT_INITIATED | user=%s | amount=%s %s | ref=%s | ip=%s",
            user.email, amount, currency, reference, ip_address or 'unknown',
            extra={
                'event': 'payment_initiated',
                'user_id': str(user.id),
                'user_email': user.email,
                'amount': str(amount),
                'currency': currency,
                'reference': reference,
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_payment_completed(user, payment_id, amount, currency, reference):
        """Journaliser la complétion d'un paiement."""
        logger.info(
            "PAYMENT_COMPLETED | user=%s | payment_id=%s | amount=%s %s | ref=%s",
            user.email, payment_id, amount, currency, reference,
            extra={
                'event': 'payment_completed',
                'user_id': str(user.id),
                'user_email': user.email,
                'payment_id': str(payment_id),
                'amount': str(amount),
                'currency': currency,
                'reference': reference,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_payment_failed(user, payment_id, reason, ip_address=None):
        """Journaliser l'échec d'un paiement."""
        logger.warning(
            "PAYMENT_FAILED | user=%s | payment_id=%s | reason=%s | ip=%s",
            user.email, payment_id, reason, ip_address or 'unknown',
            extra={
                'event': 'payment_failed',
                'user_id': str(user.id),
                'user_email': user.email,
                'payment_id': str(payment_id),
                'reason': reason,
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_webhook_received(event_type, reference, signature_valid):
        """Journaliser la réception d'un webhook."""
        level = logging.INFO if signature_valid else logging.ERROR
        logger.log(
            level,
            "WEBHOOK_RECEIVED | event=%s | ref=%s | signature_valid=%s",
            event_type, reference, signature_valid,
            extra={
                'event': 'webhook_received',
                'webhook_event': event_type,
                'reference': reference,
                'signature_valid': signature_valid,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_invalid_signature(ip_address, endpoint):
        """Journaliser une tentative avec signature invalide."""
        logger.error(
            "INVALID_SIGNATURE | ip=%s | endpoint=%s",
            ip_address or 'unknown', endpoint,
            extra={
                'event': 'invalid_signature',
                'ip_address': ip_address,
                'endpoint': endpoint,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_subscription_action(user, action, plan_name, ip_address=None):
        """Journaliser une action sur un abonnement (souscription, annulation, upgrade)."""
        logger.info(
            "SUBSCRIPTION_%s | user=%s | plan=%s | ip=%s",
            action.upper(), user.email, plan_name, ip_address or 'unknown',
            extra={
                'event': f'subscription_{action.lower()}',
                'user_id': str(user.id),
                'user_email': user.email,
                'plan_name': plan_name,
                'action': action,
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat(),
            }
        )

    @staticmethod
    def log_rate_limit_exceeded(user, action, ip_address=None):
        """Journaliser un dépassement de rate limit."""
        logger.warning(
            "RATE_LIMIT_EXCEEDED | user=%s | action=%s | ip=%s",
            user.email, action, ip_address or 'unknown',
            extra={
                'event': 'rate_limit_exceeded',
                'user_id': str(user.id),
                'user_email': user.email,
                'action': action,
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat(),
            }
        )


# ---------------------------------------------------------------------------
# Validation des paiements
# ---------------------------------------------------------------------------

class PaymentValidator:
    """
    Valide les données de paiement avant traitement.
    """

    @staticmethod
    def validate_amount(amount, currency: str) -> Tuple[bool, str]:
        """
        Valider le montant d'un paiement.

        Args:
            amount: Montant à valider (Decimal ou convertible)
            currency: Code devise (XAF, EUR, USD)

        Returns:
            (is_valid, error_message)
        """
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            return False, "Montant invalide."

        if amount <= 0:
            return False, "Le montant doit être supérieur à zéro."

        # Convertir en XAF pour vérifier les limites globales
        rate = CURRENCY_TO_XAF.get(currency.upper(), Decimal('1'))
        amount_in_xaf = amount * rate

        if amount_in_xaf < MIN_PAYMENT_AMOUNT_XAF:
            return False, (
                f"Montant trop faible. Minimum : "
                f"{MIN_PAYMENT_AMOUNT_XAF / rate:.2f} {currency}."
            )

        if amount_in_xaf > MAX_PAYMENT_AMOUNT_XAF:
            return False, (
                f"Montant trop élevé. Maximum : "
                f"{MAX_PAYMENT_AMOUNT_XAF / rate:.2f} {currency}."
            )

        return True, ""

    @staticmethod
    def validate_currency(currency: str) -> Tuple[bool, str]:
        """
        Valider le code devise.

        Returns:
            (is_valid, error_message)
        """
        if not currency or not isinstance(currency, str):
            return False, "Devise manquante."

        if currency.upper() not in ACCEPTED_CURRENCIES:
            return False, (
                f"Devise '{currency}' non supportée. "
                f"Devises acceptées : {', '.join(sorted(ACCEPTED_CURRENCIES))}."
            )

        return True, ""

    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """
        Valider le format d'un numéro de téléphone pour My-CoolPay.

        Returns:
            (is_valid, error_message)
        """
        if not phone:
            return False, "Numéro de téléphone manquant."

        # Nettoyer le numéro
        cleaned = phone.strip().replace(' ', '').replace('-', '')

        if not cleaned.startswith('+'):
            return False, "Le numéro doit commencer par + (ex: +237690000000)."

        digits_only = cleaned[1:]  # Retirer le +
        if not digits_only.isdigit():
            return False, "Le numéro ne doit contenir que des chiffres après le +."

        if len(digits_only) < 9:
            return False, "Numéro de téléphone trop court (minimum 9 chiffres)."

        if len(digits_only) > 15:
            return False, "Numéro de téléphone trop long (maximum 15 chiffres)."

        return True, ""

    @staticmethod
    def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Valider la signature HMAC-SHA256 d'un webhook My-CoolPay.

        Args:
            payload: Corps brut de la requête (bytes)
            signature: Signature reçue dans le header
            secret: Secret partagé avec My-CoolPay

        Returns:
            True si la signature est valide
        """
        if not signature or not secret:
            return False

        try:
            expected = hmac.new(
                key=secret.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha256
            ).hexdigest()

            # Comparaison sécurisée contre les timing attacks
            return hmac.compare_digest(expected, signature)

        except Exception as e:
            logger.exception("Erreur lors de la validation de la signature webhook : %s", e)
            return False


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

class PaymentRateLimiter:
    """
    Contrôle le nombre de tentatives de paiement par utilisateur.
    Utilise le cache Django (Redis en production).
    """

    @staticmethod
    def _get_cache_key(user_id: str, action: str, window: str) -> str:
        return f"payment_rate_limit:{action}:{user_id}:{window}"

    @staticmethod
    def check_payment_attempts(user) -> Tuple[bool, str]:
        """
        Vérifier si l'utilisateur n'a pas dépassé la limite de tentatives de paiement.

        Returns:
            (allowed, error_message)
        """
        now = timezone.now()
        window = now.strftime('%Y%m%d%H')  # Fenêtre horaire
        cache_key = PaymentRateLimiter._get_cache_key(str(user.id), 'payment', window)

        attempts = cache.get(cache_key, 0)

        if attempts >= MAX_PAYMENT_ATTEMPTS_PER_HOUR:
            PaymentAuditLogger.log_rate_limit_exceeded(user, 'payment_initiation')
            return False, (
                f"Trop de tentatives de paiement. "
                f"Limite : {MAX_PAYMENT_ATTEMPTS_PER_HOUR} par heure. "
                f"Réessayez dans quelques minutes."
            )

        # Incrémenter le compteur (expire après 1 heure)
        cache.set(cache_key, attempts + 1, timeout=3600)
        return True, ""

    @staticmethod
    def check_subscription_attempts(user) -> Tuple[bool, str]:
        """
        Vérifier si l'utilisateur n'a pas dépassé la limite de souscriptions.

        Returns:
            (allowed, error_message)
        """
        now = timezone.now()
        window = now.strftime('%Y%m%d')  # Fenêtre journalière
        cache_key = PaymentRateLimiter._get_cache_key(str(user.id), 'subscription', window)

        attempts = cache.get(cache_key, 0)

        if attempts >= MAX_SUBSCRIPTION_ATTEMPTS_PER_DAY:
            PaymentAuditLogger.log_rate_limit_exceeded(user, 'subscription')
            return False, (
                f"Trop de tentatives de souscription. "
                f"Limite : {MAX_SUBSCRIPTION_ATTEMPTS_PER_DAY} par jour."
            )

        cache.set(cache_key, attempts + 1, timeout=86400)
        return True, ""

    @staticmethod
    def reset_attempts(user, action: str):
        """
        Réinitialiser le compteur de tentatives (après succès).
        Utile pour ne pas pénaliser les utilisateurs légitimes.
        """
        now = timezone.now()
        if action == 'payment':
            window = now.strftime('%Y%m%d%H')
        else:
            window = now.strftime('%Y%m%d')

        cache_key = PaymentRateLimiter._get_cache_key(str(user.id), action, window)
        cache.delete(cache_key)


# ---------------------------------------------------------------------------
# Utilitaire principal
# ---------------------------------------------------------------------------

class PaymentSecurityService:
    """
    Façade regroupant toutes les vérifications de sécurité pour les paiements.
    """

    audit = PaymentAuditLogger
    validator = PaymentValidator
    rate_limiter = PaymentRateLimiter

    @classmethod
    def validate_payment_request(
        cls,
        user,
        amount,
        currency: str,
        phone_number: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validation complète d'une demande de paiement.

        Vérifie dans l'ordre :
        1. Rate limiting
        2. Devise
        3. Montant
        4. Numéro de téléphone

        Returns:
            (is_valid, error_message)
        """
        # 1. Rate limiting
        allowed, error = cls.rate_limiter.check_payment_attempts(user)
        if not allowed:
            return False, error

        # 2. Devise
        valid, error = cls.validator.validate_currency(currency)
        if not valid:
            return False, error

        # 3. Montant
        valid, error = cls.validator.validate_amount(amount, currency)
        if not valid:
            return False, error

        # 4. Numéro de téléphone
        valid, error = cls.validator.validate_phone_number(phone_number)
        if not valid:
            return False, error

        return True, ""

    @classmethod
    def get_client_ip(cls, request) -> str:
        """Extraire l'adresse IP réelle du client depuis la requête Django."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
