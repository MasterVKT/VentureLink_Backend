"""
Utilitaires pour la gestion des devises.
"""


# Liste des devises supportées par l'application
CURRENCIES = {
    'EUR': {
        'name': 'Euro',
        'symbol': '€',
        'code': 'EUR',
    },
    'USD': {
        'name': 'Dollar américain',
        'symbol': '$',
        'code': 'USD',
    },
    'GBP': {
        'name': 'Livre sterling',
        'symbol': '£',
        'code': 'GBP',
    },
    'CAD': {
        'name': 'Dollar canadien',
        'symbol': 'C$',
        'code': 'CAD',
    },
    'CHF': {
        'name': 'Franc suisse',
        'symbol': 'CHF',
        'code': 'CHF',
    },
    'JPY': {
        'name': 'Yen japonais',
        'symbol': '¥',
        'code': 'JPY',
    },
    'XOF': {
        'name': 'Franc CFA (BCEAO)',
        'symbol': 'FCFA',
        'code': 'XOF',
    },
    'XAF': {
        'name': 'Franc CFA (BEAC)',
        'symbol': 'FCFA',
        'code': 'XAF',
    },
    'MAD': {
        'name': 'Dirham marocain',
        'symbol': 'DH',
        'code': 'MAD',
    },
}


def get_currency_choices():
    """
    Retourne les choix de devises pour les formulaires.
    
    Returns:
        list: Liste de tuples (code, nom) pour chaque devise supportée
    """
    return [(code, f"{info['name']} ({info['symbol']})") for code, info in CURRENCIES.items()]


def get_currency_symbol(currency_code):
    """
    Retourne le symbole d'une devise à partir de son code.
    
    Args:
        currency_code (str): Code ISO de la devise (EUR, USD, etc.)
        
    Returns:
        str: Symbole de la devise ou le code si la devise n'est pas trouvée
    """
    if currency_code in CURRENCIES:
        return CURRENCIES[currency_code]['symbol']
    return currency_code


def convert_currency(amount, from_currency, to_currency):
    """
    Convertit un montant d'une devise à une autre.
    
    Note: Cette fonction est un placeholder qui devrait être remplacée par
    une implémentation réelle utilisant une API de taux de change.
    
    Args:
        amount (Decimal): Montant à convertir
        from_currency (str): Code de la devise source
        to_currency (str): Code de la devise cible
        
    Returns:
        Decimal: Montant converti
    """
    # Pour l'instant, utilisons des taux de change fixes pour le développement
    # Dans une version de production, cela devrait utiliser une API externe
    rates = {
        'EUR': 1.0,
        'USD': 1.1,
        'GBP': 0.85,
        'CAD': 1.5,
        'CHF': 0.95,
        'JPY': 160.0,
        'XOF': 655.957,
        'XAF': 655.957,
        'MAD': 10.8,
    }
    
    if from_currency == to_currency:
        return amount
    
    # Convertir en EUR comme monnaie intermédiaire
    amount_in_eur = amount / rates[from_currency] if from_currency in rates else amount
    
    # Puis convertir de EUR à la devise cible
    return amount_in_eur * rates[to_currency] if to_currency in rates else amount_in_eur 