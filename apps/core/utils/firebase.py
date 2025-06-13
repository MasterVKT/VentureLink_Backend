"""
Utilitaires pour l'intégration avec Firebase.
"""
import os
import json
import jwt
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from django.conf import settings
import logging


# Initialiser Firebase Admin SDK si c'est possible
firebase_app = None
try:
    # Chemin vers le fichier de configuration de Firebase Admin SDK
    firebase_creds_path = os.path.join(settings.BASE_DIR, 'config', 'firebase-admin-sdk.json')
    
    if os.path.exists(firebase_creds_path):
        # Vérifier si le fichier contient des placeholders
        with open(firebase_creds_path, 'r') as f:
            content = f.read()
            if 'placeholder' in content.lower() or 'firebase-private-key-placeholder' in content:
                print("Firebase Admin SDK : fichier de certificat contient des placeholders, mode mock activé")
            else:
                cred = credentials.Certificate(firebase_creds_path)
                firebase_app = firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialisé avec succès")
    else:
        # En mode développement, utiliser une configuration par défaut ou un mode mock
        print("Firebase Admin SDK : fichier de certificat non trouvé, mode mock activé")
        # L'utilisation d'un certificate factice peut être cause d'erreurs,
        # nous n'initialisons pas Firebase en développement si le certificat n'existe pas
except Exception as e:
    print(f"Erreur d'initialisation de Firebase Admin SDK: {e}")
    # En cas d'erreur, nous n'initialisons pas Firebase
    firebase_app = None


def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Vérifie un token ID Firebase et renvoie les informations de l'utilisateur.
    
    Args:
        id_token (str): Le token ID Firebase à vérifier
    
    Returns:
        Dict[str, Any]: Les informations de l'utilisateur extraites du token
    
    Raises:
        ValueError: Si le token est invalide ou si Firebase n'est pas configuré
    """
    logger = logging.getLogger(__name__)
    
    if not id_token:
        logger.error("Token Firebase vide ou invalide")
        raise ValueError("Token Firebase vide ou invalide")
        
    if not firebase_app:
        # En mode développement, utiliser une vérification basique
        if settings.DEBUG:
            logger.debug("Firebase Admin SDK n'est pas initialisé, utilisation de la vérification basique en développement")
            return verify_firebase_token_dev_mode(id_token)
        logger.error("Firebase Admin SDK n'est pas initialisé")
        raise ValueError("Firebase Admin SDK n'est pas initialisé")
    
    try:
        # Vérifier le token ID
        decoded_token = firebase_auth.verify_id_token(id_token)
        
        # Extraire les informations pertinentes
        user_info = {
            'uid': decoded_token.get('uid'),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False),
            'provider_id': decoded_token.get('firebase', {}).get('sign_in_provider'),
        }
        
        # Journaliser les informations de succès
        logger.info(f"Token Firebase vérifié avec succès pour l'utilisateur {user_info['email']}")
        
        return user_info
    except firebase_admin.exceptions.ExpiredIdTokenError:
        logger.warning("Token Firebase expiré")
        raise ValueError("Token Firebase expiré")
    except firebase_admin.exceptions.InvalidIdTokenError:
        logger.warning("Token Firebase invalide")
        raise ValueError("Token Firebase invalide ou mal formé")
    except firebase_admin.exceptions.RevokedIdTokenError:
        logger.warning("Token Firebase révoqué")
        raise ValueError("Token Firebase révoqué")
    except Exception as e:
        # En mode développement, essayer la vérification basique en cas d'échec
        if settings.DEBUG:
            logger.warning(f"Erreur de vérification du token Firebase: {str(e)}")
            logger.debug("Tentative de vérification basique en mode développement")
            return verify_firebase_token_dev_mode(id_token)
        logger.error(f"Erreur de vérification du token Firebase: {str(e)}")
        raise ValueError(f"Token Firebase invalide: {str(e)}")


def verify_firebase_token_dev_mode(id_token: str) -> Dict[str, Any]:
    """
    Vérification basique du token Firebase en mode développement.
    Cette méthode decode le JWT sans vérification de signature.
    
    ATTENTION: À utiliser uniquement en mode développement !
    
    Args:
        id_token (str): Le token ID Firebase à vérifier
    
    Returns:
        Dict[str, Any]: Les informations de l'utilisateur extraites du token
    
    Raises:
        ValueError: Si le token est invalide même sans vérification
    """
    try:
        # Decode sans vérification de signature (UNIQUEMENT pour le développement)
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        
        # Vérifications basiques
        if 'iss' in decoded_token:
            project_id = settings.FIREBASE_CONFIG.get('projectId', '')
            if project_id and decoded_token.get('iss') != f'https://securetoken.google.com/{project_id}':
                print(f"Avertissement: Token issuer ne correspond pas au projet configuré")
        
        # Vérifier que le token n'est pas expiré
        if decoded_token.get('exp', 0) < time.time():
            print("Avertissement: Token expiré, mais accepté en mode développement")
        
        # Extraire les informations pertinentes
        user_info = {
            'uid': decoded_token.get('sub', decoded_token.get('user_id')),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False),
            'provider_id': decoded_token.get('firebase', {}).get('sign_in_provider'),
        }
        
        return user_info
    except Exception as e:
        raise ValueError(f"Token Firebase invalide même en mode développement: {str(e)}")


def get_firebase_user(uid: str) -> Dict[str, Any]:
    """
    Récupère les informations d'un utilisateur Firebase par son UID.
    
    Args:
        uid (str): L'UID de l'utilisateur Firebase
    
    Returns:
        Dict[str, Any]: Les informations de l'utilisateur
    
    Raises:
        ValueError: Si l'utilisateur n'existe pas ou si Firebase n'est pas configuré
    """
    if not firebase_app:
        # En mode développement, retourner des données fictives
        if settings.DEBUG:
            print("Firebase Admin SDK n'est pas initialisé, retour de données fictives en développement")
            return {
                'uid': uid,
                'email': f"user-{uid}@example.com",
                'display_name': f"Utilisateur {uid}",
                'photo_url': None,
                'email_verified': True,
                'disabled': False,
                'created_at': int(time.time() * 1000),
            }
        raise ValueError("Firebase Admin SDK n'est pas initialisé")
    
    try:
        user = firebase_auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'email_verified': user.email_verified,
            'disabled': user.disabled,
            'created_at': user.user_metadata.creation_timestamp,
        }
    except Exception as e:
        raise ValueError(f"Erreur lors de la récupération de l'utilisateur Firebase: {str(e)}")


def create_firebase_custom_token(uid: str, claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Crée un token personnalisé Firebase pour l'authentification côté serveur.
    
    Args:
        uid (str): L'UID de l'utilisateur Firebase
        claims (Dict[str, Any], optional): Les revendications personnalisées à inclure
    
    Returns:
        str: Le token personnalisé
    
    Raises:
        ValueError: Si Firebase n'est pas configuré
    """
    if not firebase_app:
        raise ValueError("Firebase Admin SDK n'est pas initialisé")
    
    try:
        return firebase_auth.create_custom_token(uid, claims or {})
    except Exception as e:
        raise ValueError(f"Erreur lors de la création du token personnalisé: {str(e)}")


def send_firebase_notification(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
    """
    Envoie une notification Firebase Cloud Messaging.
    
    Args:
        token (str): Le token FCM du destinataire
        title (str): Le titre de la notification
        body (str): Le corps de la notification
        data (Dict[str, str], optional): Données supplémentaires à envoyer
    
    Returns:
        bool: True si l'envoi a réussi, False sinon
    
    Note:
        Cette fonction est un placeholder qui devra être implémentée avec la bibliothèque FCM.
    """
    # Placeholder pour l'implémentation de FCM
    # Cette fonction devra être implémentée avec la bibliothèque firebase-admin
    # ou une autre bibliothèque compatible avec FCM
    return False 