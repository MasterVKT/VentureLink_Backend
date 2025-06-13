import os
import uuid
import logging
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)


def generate_unique_filename(instance, filename):
    """
    Génère un nom de fichier unique pour les uploads.
    
    Args:
        instance: Instance du modèle
        filename: Nom du fichier original
    
    Returns:
        Chemin du fichier avec un nom unique
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Obtenir le nom du modèle en minuscules pour le chemin
    model_name = instance.__class__.__name__.lower()
    
    # Utiliser l'ID de l'instance si disponible, sinon générer un UUID temporaire
    instance_id = getattr(instance, 'id', uuid.uuid4())
    
    return f"{model_name}/{instance_id}/{new_filename}"


def get_file_path(instance, filename, subfolder=None):
    """
    Retourne un chemin de fichier pour les uploads en utilisant une structure organisée.
    
    Args:
        instance: Instance du modèle
        filename: Nom du fichier original
        subfolder: Sous-dossier optionnel (ex: 'avatars', 'documents')
    
    Returns:
        Chemin du fichier
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Obtenir le nom du modèle
    model_name = instance.__class__.__name__.lower()
    
    # Construire le chemin
    if subfolder:
        return f"uploads/{model_name}/{subfolder}/{filename}"
    
    return f"uploads/{model_name}/{filename}"


def initialize_firebase():
    """
    Initialise Firebase Admin SDK s'il n'est pas déjà initialisé.
    
    Returns:
        Instance Firebase
    """
    try:
        # Vérifier si Firebase est déjà initialisé
        return firebase_admin.get_app()
    except ValueError:
        # Initialiser Firebase
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        
        if not cred_path or not os.path.exists(cred_path):
            logger.warning("Chemin des identifiants Firebase non trouvé")
            return None
        
        try:
            cred = credentials.Certificate(cred_path)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Firebase: {str(e)}")
            return None


def verify_firebase_token(token):
    """
    Vérifie un token Firebase.
    
    Args:
        token: Token Firebase à vérifier
    
    Returns:
        Données utilisateur décodées ou None en cas d'erreur
    """
    app = initialize_firebase()
    if not app:
        return None
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token Firebase: {str(e)}")
        return None


def get_currency_choices():
    """
    Retourne les choix de devises disponibles dans l'application.
    
    Returns:
        Liste de tuples (code devise, nom devise)
    """
    currencies = getattr(settings, 'CURRENCIES', ('EUR', 'USD', 'GBP'))
    
    # Dictionnaire de noms de devises (pour l'affichage)
    currency_names = {
        'EUR': 'Euro (€)',
        'USD': 'Dollar américain ($)',
        'GBP': 'Livre sterling (£)',
        'CAD': 'Dollar canadien ($)',
        'CHF': 'Franc suisse (CHF)',
        'AUD': 'Dollar australien ($)',
        'JPY': 'Yen japonais (¥)',
    }
    
    return [(code, currency_names.get(code, code)) for code in currencies]


def convert_currency(amount, from_currency, to_currency):
    """
    Convertit un montant d'une devise à une autre.
    Dans une implémentation réelle, cela utiliserait une API de taux de change.
    
    Args:
        amount: Montant à convertir
        from_currency: Devise source
        to_currency: Devise cible
    
    Returns:
        Montant converti
    """
    if from_currency == to_currency:
        return amount
    
    # Taux de change factices pour démonstration
    # Dans une implémentation réelle, utilisez une API comme Open Exchange Rates
    rates = {
        'EUR': {'USD': 1.10, 'GBP': 0.85, 'EUR': 1.0},
        'USD': {'EUR': 0.91, 'GBP': 0.77, 'USD': 1.0},
        'GBP': {'EUR': 1.18, 'USD': 1.30, 'GBP': 1.0},
    }
    
    try:
        conversion_rate = rates.get(from_currency, {}).get(to_currency)
        if not conversion_rate:
            return amount  # Retourner le montant original si le taux n'est pas disponible
        
        return amount * conversion_rate
    except (TypeError, ValueError):
        return amount 