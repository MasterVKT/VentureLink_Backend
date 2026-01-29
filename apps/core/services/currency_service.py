"""
Service de conversion de devises.
"""
import logging
import requests
from typing import Dict, Union, Optional
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CurrencyService:
    """
    Service pour gérer la conversion de devises.
    
    Ce service permet de convertir des montants entre différentes devises
    en utilisant un service d'API externe pour obtenir les taux de change.
    """
    
    # Durée de mise en cache des taux de change (24h par défaut)
    CACHE_TIMEOUT = 60 * 60 * 24
    
    # Clé de cache pour les taux de change
    EXCHANGE_RATES_CACHE_KEY = 'currency_exchange_rates'
    
    def __init__(self):
        """
        Initialise le service de conversion de devises.
        """
        self.api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
        self.api_url = getattr(settings, 'EXCHANGE_RATE_API_URL', 'https://api.exchangerate-api.com/v4/latest/')
        self.default_currency = getattr(settings, 'DEFAULT_CURRENCY', 'EUR')
    
    def get_exchange_rates(self, base_currency: str = None) -> Dict[str, float]:
        """
        Récupère les taux de change depuis l'API ou le cache.
        
        Args:
            base_currency (str, optional): Devise de base pour les taux de change
                
        Returns:
            Dict[str, float]: Dictionnaire des taux de change
        """
        base_currency = base_currency or self.default_currency
        cache_key = f"{self.EXCHANGE_RATES_CACHE_KEY}_{base_currency}"
        
        # Essayer de récupérer les taux depuis le cache
        cached_rates = cache.get(cache_key)
        if cached_rates:
            return cached_rates
        
        try:
            # Si pas en cache, appeler l'API
            url = f"{self.api_url}{base_currency}"
            if self.api_key:
                url = f"{url}?access_key={self.api_key}"
                
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            
            # Mettre en cache les taux de change
            if rates:
                cache.set(cache_key, rates, self.CACHE_TIMEOUT)
                
            return rates
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des taux de change: {str(e)}")
            # En cas d'erreur, retourner un dictionnaire vide
            return {}
    
    def convert_currency(
        self, 
        amount: Union[float, Decimal], 
        from_currency: str, 
        to_currency: str
    ) -> Union[float, Decimal]:
        """
        Convertit un montant d'une devise à une autre.
        
        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            
        Returns:
            float/Decimal: Montant converti
        """
        # Si les devises sont identiques, retourner le montant d'origine
        if from_currency == to_currency or amount is None:
            return amount
        
        # Standardiser les codes de devise
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Obtenir les taux de change
        exchange_rates = self.get_exchange_rates(self.default_currency)
        
        if not exchange_rates:
            logger.warning("Impossible de convertir la devise: taux de change non disponibles")
            return amount
        
        # Obtenir les taux pour les devises source et cible
        from_rate = exchange_rates.get(from_currency)
        to_rate = exchange_rates.get(to_currency)
        
        if not from_rate or not to_rate:
            logger.warning(f"Taux de change non disponible pour {from_currency} ou {to_currency}")
            return amount
        
        # Calculer le montant converti
        # 1. Convertir de la devise source vers la devise de base (EUR par défaut)
        base_amount = float(amount) / from_rate
        # 2. Convertir de la devise de base vers la devise cible
        converted_amount = base_amount * to_rate
        
        # Si le montant était un Decimal, retourner un Decimal
        if isinstance(amount, Decimal):
            return Decimal(str(round(converted_amount, 2)))
        
        # Sinon retourner un float
        return round(converted_amount, 2)
    
    def get_available_currencies(self) -> Dict[str, str]:
        """
        Récupère la liste des devises disponibles.
        
        Returns:
            Dict[str, str]: Dictionnaire des devises disponibles (code: nom)
        """
        # Liste statique des devises les plus courantes
        # Dans une application réelle, cela pourrait provenir d'une API
        return {
            'EUR': 'Euro',
            'USD': 'Dollar américain',
            'GBP': 'Livre sterling',
            'JPY': 'Yen japonais',
            'CAD': 'Dollar canadien',
            'AUD': 'Dollar australien',
            'CHF': 'Franc suisse',
            'CNY': 'Yuan chinois',
            'HKD': 'Dollar de Hong Kong',
            'NZD': 'Dollar néo-zélandais',
            'SEK': 'Couronne suédoise',
            'KRW': 'Won sud-coréen',
            'SGD': 'Dollar de Singapour',
            'NOK': 'Couronne norvégienne',
            'MXN': 'Peso mexicain',
            'INR': 'Roupie indienne',
            'RUB': 'Rouble russe',
            'ZAR': 'Rand sud-africain',
            'BRL': 'Real brésilien',
            'TRY': 'Livre turque',
        }
    
    def format_currency(self, amount: Union[float, Decimal], currency: str) -> str:
        """
        Formate un montant avec son symbole de devise.
        
        Args:
            amount: Montant à formater
            currency: Code ISO de la devise
            
        Returns:
            str: Montant formaté avec symbole de devise
        """
        if amount is None:
            return "-"
            
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'CAD': 'CA$',
            'AUD': 'A$',
            'CHF': 'CHF',
            'CNY': '¥',
            'HKD': 'HK$',
            'NZD': 'NZ$',
        }
        
        # Récupérer le symbole de la devise ou utiliser le code ISO
        symbol = currency_symbols.get(currency.upper(), currency.upper())
        
        # Formater le montant avec deux décimales
        formatted_amount = f"{float(amount):,.2f}".replace(',', ' ')
        
        # Retourner le montant formaté avec le symbole de la devise
        if currency.upper() in ['EUR', 'GBP']:
            return f"{formatted_amount} {symbol}"  # Symbole après le montant
        else:
            return f"{symbol}{formatted_amount}"   # Symbole avant le montant
    
    @classmethod
    def convert_amount(
        cls, 
        amount: Union[float, Decimal], 
        from_currency: str, 
        to_currency: str
    ) -> Union[float, Decimal]:
        """
        Méthode de classe pour convertir un montant d'une devise à une autre.
        Alias pour convert_currency pour rétrocompatibilité.
        
        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            
        Returns:
            float/Decimal: Montant converti
        """
        service = cls()
        return service.convert_currency(amount, from_currency, to_currency) 