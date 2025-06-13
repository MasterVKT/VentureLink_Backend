"""
Utilitaires pour la gestion des tokens d'authentification.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple


def generate_token(identifier: str, expiry_days: int = 1) -> Tuple[str, str]:
    """
    Génère un token d'authentification avec une date d'expiration.
    
    Args:
        identifier (str): Un identifiant unique (généralement l'ID de l'utilisateur)
        expiry_days (int): Durée de validité du token en jours
    
    Returns:
        Tuple[str, str]: Un tuple contenant le token et sa signature
    """
    # Générer un token aléatoire
    random_token = secrets.token_hex(32)
    
    # Calculer la date d'expiration
    expiry = datetime.now() + timedelta(days=expiry_days)
    expiry_timestamp = int(expiry.timestamp())
    
    # Créer la signature
    signature_base = f"{random_token}:{identifier}:{expiry_timestamp}"
    signature = hashlib.sha256(signature_base.encode()).hexdigest()
    
    # Le token final est une combinaison du token aléatoire et de la signature
    token = f"{random_token}.{expiry_timestamp}"
    
    return token, signature


def validate_token(token: str, signature: str, identifier: str) -> bool:
    """
    Valide un token d'authentification.
    
    Args:
        token (str): Le token à valider
        signature (str): La signature du token
        identifier (str): L'identifiant associé au token (généralement l'ID de l'utilisateur)
    
    Returns:
        bool: True si le token est valide, False sinon
    """
    try:
        # Séparer le token en ses composants
        random_token, expiry_timestamp = token.split('.')
        expiry_timestamp = int(expiry_timestamp)
        
        # Vérifier si le token a expiré
        current_timestamp = int(datetime.now().timestamp())
        if current_timestamp > expiry_timestamp:
            return False
        
        # Recréer la signature et vérifier
        signature_base = f"{random_token}:{identifier}:{expiry_timestamp}"
        calculated_signature = hashlib.sha256(signature_base.encode()).hexdigest()
        
        return calculated_signature == signature
    except (ValueError, TypeError):
        # En cas d'erreur dans le format du token
        return False 