"""
Service de conversion de devises — Sprint 3 B3.5 : Multi-Devises.

Responsabilités :
- Taux de change fixes XAF/EUR/USD (priorité 1 — toujours disponibles)
- Taux dynamiques via API externe avec cache Redis (priorité 2)
- Formatage des montants avec symboles
- Détection de la devise préférée de l'utilisateur
"""
import logging
import requests
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Union, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes — Devises supportées par VentureLink
# ---------------------------------------------------------------------------

# Devises principales de la plateforme (XAF en priorité pour l'Afrique centrale)
VENTURELINK_CURRENCIES = {
    'XAF': 'Franc CFA (BEAC)',
    'EUR': 'Euro',
    'USD': 'Dollar américain',
}

# Toutes les devises disponibles (pour la liste complète)
ALL_SUPPORTED_CURRENCIES = {
    'XAF': 'Franc CFA (BEAC)',
    'EUR': 'Euro',
    'USD': 'Dollar américain',
    'GBP': 'Livre sterling',
    'CAD': 'Dollar canadien',
    'CHF': 'Franc suisse',
    'JPY': 'Yen japonais',
    'AUD': 'Dollar australien',
    'CNY': 'Yuan chinois',
    'NGN': 'Naira nigérian',
    'GHS': 'Cedi ghanéen',
    'KES': 'Shilling kényan',
    'ZAR': 'Rand sud-africain',
    'MAD': 'Dirham marocain',
    'TND': 'Dinar tunisien',
    'XOF': 'Franc CFA (BCEAO)',
}

# Symboles des devises
CURRENCY_SYMBOLS = {
    'XAF': 'FCFA',
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'CAD': 'CA$',
    'CHF': 'CHF',
    'JPY': '¥',
    'AUD': 'A$',
    'CNY': '¥',
    'NGN': '₦',
    'GHS': 'GH₵',
    'KES': 'KSh',
    'ZAR': 'R',
    'MAD': 'MAD',
    'TND': 'DT',
    'XOF': 'FCFA',
}

# ---------------------------------------------------------------------------
# Taux de change fixes XAF/EUR/USD
# Ces taux sont utilisés comme fallback quand l'API externe est indisponible.
# Le taux EUR/XAF est fixé par la Banque de France (parité fixe).
# ---------------------------------------------------------------------------

# Taux de base : 1 EUR = X unités de la devise cible
FIXED_RATES_FROM_EUR = {
    'EUR': Decimal('1'),
    'XAF': Decimal('655.957'),   # Parité fixe officielle EUR/XAF
    'XOF': Decimal('655.957'),   # Même parité (zone franc BCEAO)
    'USD': Decimal('1.08'),      # Approximatif — mis à jour via API
    'GBP': Decimal('0.86'),
    'CAD': Decimal('1.47'),
    'CHF': Decimal('0.97'),
    'JPY': Decimal('162.0'),
    'AUD': Decimal('1.64'),
    'CNY': Decimal('7.82'),
    'NGN': Decimal('1620.0'),
    'GHS': Decimal('16.5'),
    'KES': Decimal('140.0'),
    'ZAR': Decimal('20.0'),
    'MAD': Decimal('10.8'),
    'TND': Decimal('3.35'),
}

# Clé de cache pour les taux dynamiques
EXCHANGE_RATES_CACHE_KEY = 'currency_exchange_rates_v2'
EXCHANGE_RATES_CACHE_TIMEOUT = 60 * 60 * 24  # 24 heures


class CurrencyService:
    """
    Service de conversion de devises pour VentureLink.

    Stratégie de résolution des taux :
    1. Cache Redis (taux dynamiques récupérés précédemment)
    2. API externe (exchangerate-api.com)
    3. Taux fixes intégrés (fallback garanti — toujours disponible)
    """

    def __init__(self):
        self.api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', '')
        self.api_url = getattr(settings, 'EXCHANGE_RATE_API_URL',
                               'https://api.exchangerate-api.com/v4/latest/')
        self.default_currency = getattr(settings, 'DEFAULT_CURRENCY', 'EUR')

    # ------------------------------------------------------------------
    # Récupération des taux de change
    # ------------------------------------------------------------------

    def get_exchange_rates(self, base_currency: str = 'EUR') -> Dict[str, Decimal]:
        """
        Retourne les taux de change depuis le cache, l'API ou les taux fixes.

        Args:
            base_currency: Devise de base (défaut : EUR)

        Returns:
            Dict[str, Decimal]: Taux de change {code_devise: taux}
        """
        base_currency = base_currency.upper()
        cache_key = f"{EXCHANGE_RATES_CACHE_KEY}_{base_currency}"

        # 1. Essayer le cache Redis
        cached = cache.get(cache_key)
        if cached:
            logger.debug("Taux de change récupérés depuis le cache pour %s", base_currency)
            return cached

        # 2. Essayer l'API externe
        rates = self._fetch_rates_from_api(base_currency)
        if rates:
            cache.set(cache_key, rates, EXCHANGE_RATES_CACHE_TIMEOUT)
            logger.info("Taux de change mis en cache pour %s (%d devises)", base_currency, len(rates))
            return rates

        # 3. Fallback : taux fixes intégrés
        logger.warning(
            "API de taux de change indisponible — utilisation des taux fixes pour %s",
            base_currency
        )
        return self._get_fixed_rates(base_currency)

    def _fetch_rates_from_api(self, base_currency: str) -> Optional[Dict[str, Decimal]]:
        """
        Récupère les taux depuis l'API externe.

        Returns:
            Dict ou None si l'API est indisponible
        """
        if not self.api_url:
            return None

        try:
            url = f"{self.api_url}{base_currency}"
            if self.api_key:
                url = f"{url}?access_key={self.api_key}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            raw_rates = data.get('rates', {})
            if not raw_rates:
                return None

            # Convertir en Decimal pour la précision
            return {
                code: Decimal(str(rate))
                for code, rate in raw_rates.items()
            }

        except requests.RequestException as e:
            logger.error("Erreur API taux de change (%s): %s", base_currency, e)
            return None
        except Exception as e:
            logger.exception("Erreur inattendue lors de la récupération des taux: %s", e)
            return None

    def _get_fixed_rates(self, base_currency: str) -> Dict[str, Decimal]:
        """
        Calcule les taux fixes à partir de la base EUR.

        Args:
            base_currency: Devise de base souhaitée

        Returns:
            Dict[str, Decimal]: Taux calculés depuis la base demandée
        """
        base_currency = base_currency.upper()

        if base_currency == 'EUR':
            return dict(FIXED_RATES_FROM_EUR)

        # Convertir depuis EUR vers la base demandée
        base_rate_from_eur = FIXED_RATES_FROM_EUR.get(base_currency)
        if not base_rate_from_eur or base_rate_from_eur == 0:
            logger.warning("Devise de base inconnue dans les taux fixes: %s", base_currency)
            return dict(FIXED_RATES_FROM_EUR)

        # Recalculer tous les taux depuis la nouvelle base
        return {
            code: (rate / base_rate_from_eur).quantize(Decimal('0.000001'))
            for code, rate in FIXED_RATES_FROM_EUR.items()
        }

    def invalidate_cache(self, base_currency: str = None):
        """
        Invalide le cache des taux de change.

        Args:
            base_currency: Si fourni, invalide uniquement cette base.
                           Sinon, invalide EUR, USD et XAF.
        """
        if base_currency:
            cache.delete(f"{EXCHANGE_RATES_CACHE_KEY}_{base_currency.upper()}")
        else:
            for currency in ['EUR', 'USD', 'XAF']:
                cache.delete(f"{EXCHANGE_RATES_CACHE_KEY}_{currency}")

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def convert(
        self,
        amount: Union[float, Decimal, int],
        from_currency: str,
        to_currency: str,
        precision: int = 2,
    ) -> Decimal:
        """
        Convertit un montant d'une devise à une autre.

        Args:
            amount: Montant à convertir
            from_currency: Code devise source (ex: 'XAF')
            to_currency: Code devise cible (ex: 'EUR')
            precision: Nombre de décimales dans le résultat

        Returns:
            Decimal: Montant converti, arrondi à `precision` décimales
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency or amount is None:
            return Decimal(str(amount)) if amount is not None else Decimal('0')

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            logger.error("Montant invalide pour la conversion: %s", amount)
            return Decimal('0')

        # Récupérer les taux depuis EUR comme base
        rates = self.get_exchange_rates('EUR')

        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)

        if not from_rate or not to_rate:
            logger.warning(
                "Taux manquant pour la conversion %s → %s",
                from_currency, to_currency
            )
            return amount

        # Conversion via EUR comme devise pivot
        # amount_in_eur = amount / from_rate
        # result = amount_in_eur * to_rate
        amount_in_eur = amount / from_rate
        result = amount_in_eur * to_rate

        # Arrondir selon la précision demandée
        quantizer = Decimal('1') / (Decimal('10') ** precision)
        return result.quantize(quantizer, rounding=ROUND_HALF_UP)

    def convert_currency(
        self,
        amount: Union[float, Decimal],
        from_currency: str,
        to_currency: str,
    ) -> Union[float, Decimal]:
        """
        Alias de `convert()` pour rétrocompatibilité avec le code existant.
        Retourne le même type que l'entrée (float ou Decimal).
        """
        result = self.convert(amount, from_currency, to_currency)
        if isinstance(amount, float):
            return float(result)
        return result

    @classmethod
    def convert_amount(
        cls,
        amount: Union[float, Decimal],
        from_currency: str,
        to_currency: str,
    ) -> Union[float, Decimal]:
        """
        Méthode de classe pour conversion rapide sans instanciation.
        Rétrocompatibilité.
        """
        return cls().convert_currency(amount, from_currency, to_currency)

    def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Retourne le taux de change entre deux devises.

        Args:
            from_currency: Devise source
            to_currency: Devise cible

        Returns:
            Decimal: Taux (1 unité de from_currency = X unités de to_currency)
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return Decimal('1')

        rates = self.get_exchange_rates('EUR')
        from_rate = rates.get(from_currency, Decimal('1'))
        to_rate = rates.get(to_currency, Decimal('1'))

        if not from_rate:
            return Decimal('1')

        return (to_rate / from_rate).quantize(Decimal('0.000001'))

    # ------------------------------------------------------------------
    # Formatage
    # ------------------------------------------------------------------

    def format_amount(self, amount: Union[float, Decimal], currency: str) -> str:
        """
        Formate un montant avec son symbole de devise.

        Args:
            amount: Montant à formater
            currency: Code ISO de la devise

        Returns:
            str: Montant formaté (ex: "5 000 FCFA", "€8.00", "$9.00")
        """
        if amount is None:
            return '-'

        currency = currency.upper()
        symbol = CURRENCY_SYMBOLS.get(currency, currency)

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return '-'

        # XAF et XOF : pas de décimales, séparateur de milliers
        if currency in ('XAF', 'XOF'):
            formatted = f"{int(amount):,}".replace(',', ' ')
            return f"{formatted} {symbol}"

        # JPY : pas de décimales
        if currency == 'JPY':
            formatted = f"{int(amount):,}".replace(',', ' ')
            return f"{symbol}{formatted}"

        # Autres devises : 2 décimales
        formatted = f"{float(amount):,.2f}".replace(',', ' ')

        # Symbole après le montant pour EUR
        if currency == 'EUR':
            return f"{formatted} {symbol}"

        # Symbole avant le montant pour USD, GBP, etc.
        return f"{symbol}{formatted}"

    def format_currency(self, amount: Union[float, Decimal], currency: str) -> str:
        """Alias de format_amount pour rétrocompatibilité."""
        return self.format_amount(amount, currency)

    def get_symbol(self, currency: str) -> str:
        """
        Retourne le symbole d'une devise.

        Args:
            currency: Code ISO de la devise

        Returns:
            str: Symbole (ex: '€', '$', 'FCFA')
        """
        return CURRENCY_SYMBOLS.get(currency.upper(), currency.upper())

    # ------------------------------------------------------------------
    # Informations sur les devises
    # ------------------------------------------------------------------

    def get_available_currencies(self) -> Dict[str, str]:
        """
        Retourne toutes les devises supportées.

        Returns:
            Dict[str, str]: {code: nom}
        """
        return dict(ALL_SUPPORTED_CURRENCIES)

    def get_venturelink_currencies(self) -> Dict[str, str]:
        """
        Retourne uniquement les devises principales de VentureLink (XAF, EUR, USD).

        Returns:
            Dict[str, str]: {code: nom}
        """
        return dict(VENTURELINK_CURRENCIES)

    def is_supported(self, currency: str) -> bool:
        """
        Vérifie si une devise est supportée.

        Args:
            currency: Code ISO de la devise

        Returns:
            bool: True si supportée
        """
        return currency.upper() in ALL_SUPPORTED_CURRENCIES

    def get_all_rates_for_display(self, base_currency: str = 'EUR') -> Dict[str, Dict]:
        """
        Retourne les taux de change formatés pour l'affichage frontend.

        Args:
            base_currency: Devise de base

        Returns:
            Dict avec taux, symboles et noms pour chaque devise
        """
        base_currency = base_currency.upper()
        rates = self.get_exchange_rates(base_currency)

        result = {}
        for code, name in ALL_SUPPORTED_CURRENCIES.items():
            rate = rates.get(code)
            if rate:
                result[code] = {
                    'code': code,
                    'name': name,
                    'symbol': CURRENCY_SYMBOLS.get(code, code),
                    'rate': str(rate),
                    'formatted_rate': self.format_amount(rate, code),
                }

        return result

    # ------------------------------------------------------------------
    # Détection de la devise utilisateur
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_preferred_currency(request) -> str:
        """
        Détermine la devise préférée de l'utilisateur depuis la requête.

        Ordre de priorité :
        1. Paramètre GET `?currency=XAF`
        2. Header `Accept-Currency: XAF`
        3. Champ `preferred_currency` sur le modèle User
        4. Devise par défaut des settings (EUR)

        Args:
            request: Requête Django

        Returns:
            str: Code ISO de la devise (3 lettres majuscules)
        """
        default = getattr(settings, 'DEFAULT_CURRENCY', 'EUR')

        # 1. Paramètre GET
        currency_param = request.GET.get('currency', '').strip().upper()
        if currency_param and len(currency_param) == 3 and currency_param in ALL_SUPPORTED_CURRENCIES:
            return currency_param

        # 2. Header HTTP
        header_currency = request.META.get('HTTP_ACCEPT_CURRENCY', '').strip().upper()
        if header_currency and len(header_currency) == 3 and header_currency in ALL_SUPPORTED_CURRENCIES:
            return header_currency

        # 3. Préférence utilisateur (champ direct sur User)
        if request.user and request.user.is_authenticated:
            user_currency = getattr(request.user, 'preferred_currency', None)
            if user_currency and user_currency.upper() in ALL_SUPPORTED_CURRENCIES:
                return user_currency.upper()

        return default
