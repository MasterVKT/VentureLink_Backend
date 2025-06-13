import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

from apps.core.utils.firebase import verify_firebase_token
from apps.core.exceptions import AuthenticationError, InvalidCredentialsError, TokenError

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthService:
    """
    Service pour gérer les opérations d'authentification.
    """
    
    @staticmethod
    def register_user(email, password, first_name, last_name, user_type='BOTH'):
        """
        Enregistre un nouvel utilisateur.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            first_name (str): Prénom
            last_name (str): Nom
            user_type (str): Type d'utilisateur
            
        Returns:
            User: L'utilisateur créé
            
        Raises:
            ValidationError: Si l'email est déjà utilisé
        """
        # La validation est gérée par le sérialiseur
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type
        )
        return user
    
    @staticmethod
    def authenticate_with_credentials(email, password):
        """
        Authentifie un utilisateur avec email et mot de passe.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            
        Returns:
            tuple: (User, access_token, refresh_token)
            
        Raises:
            InvalidCredentialsError: Si les identifiants sont invalides
        """
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                raise InvalidCredentialsError()
                
            if not user.is_active:
                raise AuthenticationError("Ce compte a été désactivé.")
            
            # Générer les tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            return user, access_token, refresh_token
        
        except User.DoesNotExist:
            raise InvalidCredentialsError()
    
    @staticmethod
    def authenticate_with_firebase(token):
        """
        Authentifie un utilisateur avec un token Firebase.
        
        Args:
            token (str): Token Firebase ID
            
        Returns:
            tuple: (User, access_token, refresh_token, is_new_user)
            
        Raises:
            AuthenticationError: Si l'authentification échoue
            TokenError: Si le token est invalide
        """
        if not token:
            logger.error("Token Firebase vide ou manquant")
            raise TokenError("Token Firebase vide ou manquant")
        
        try:
            # Vérification du token Firebase
            decoded_token = verify_firebase_token(token)
            
            if not decoded_token:
                logger.error("Échec de vérification du token Firebase")
                raise TokenError("Token Firebase invalide")
            
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            
            if not firebase_uid:
                logger.error("Token Firebase sans UID")
                raise AuthenticationError("Le token Firebase ne contient pas d'UID.")
            
            if not email:
                logger.error(f"Token Firebase sans email pour l'UID {firebase_uid}")
                raise AuthenticationError("Le token Firebase ne contient pas d'email.")
            
            # Récupérer ou créer l'utilisateur
            user, is_new_user = AuthService.get_or_create_firebase_user(
                firebase_uid=firebase_uid,
                email=email,
                first_name=decoded_token.get('name', '').split(' ')[0] if decoded_token.get('name') else '',
                last_name=' '.join(decoded_token.get('name', '').split(' ')[1:]) if decoded_token.get('name') else '',
                profile_picture=decoded_token.get('picture')
            )
            
            # Vérifier si l'utilisateur est actif
            if not user.is_active:
                logger.warning(f"Tentative de connexion avec un compte désactivé: {email}")
                raise AuthenticationError("Ce compte a été désactivé.")
            
            # Générer les tokens
            refresh = RefreshToken.for_user(user)
            
            # Ajouter des revendications personnalisées au token
            refresh['firebase_uid'] = firebase_uid
            refresh['email'] = email
            refresh['is_verified'] = user.is_verified
            refresh['user_type'] = user.user_type
            
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Journaliser le succès de l'authentification
            logger.info(f"Authentification Firebase réussie pour {email} (UID: {firebase_uid})")
            
            return user, access_token, refresh_token, is_new_user
            
        except TokenError as e:
            # Propager l'erreur TokenError telle quelle
            raise
        except AuthenticationError as e:
            # Propager l'erreur AuthenticationError telle quelle
            raise
        except Exception as e:
            logger.error(f"Erreur d'authentification Firebase: {str(e)}")
            raise AuthenticationError(f"Erreur d'authentification Firebase: {str(e)}")
    
    @staticmethod
    def get_or_create_firebase_user(firebase_uid, email, first_name='', last_name='', profile_picture=None):
        """
        Récupère ou crée un utilisateur à partir des informations Firebase.
        
        Args:
            firebase_uid (str): L'identifiant Firebase de l'utilisateur
            email (str): L'adresse e-mail de l'utilisateur
            first_name (str, optional): Le prénom de l'utilisateur
            last_name (str, optional): Le nom de l'utilisateur
            profile_picture (str, optional): L'URL de la photo de profil
            
        Returns:
            tuple: (User, is_new_user) - L'utilisateur et un booléen indiquant s'il a été créé
        """
        try:
            # Vérifier si l'utilisateur existe déjà
            user = User.objects.get(email=email)
            
            # Mettre à jour les noms si nécessaires et s'ils sont vides
            updated_fields = []
                
            if first_name and not user.first_name:
                user.first_name = first_name
                updated_fields.append('first_name')
                
            if last_name and not user.last_name:
                user.last_name = last_name
                updated_fields.append('last_name')
                
            # Sauvegarder les modifications si nécessaire
            if updated_fields:
                user.save(update_fields=updated_fields)
                
            # Note: Nous n'avons pas besoin de créer un profil car un signal le fait déjà 
            # automatiquement lors de la création de l'utilisateur
                
            return user, False
            
        except User.DoesNotExist:
            # Créer un nouvel utilisateur
            user = User.objects.create_user(
                email=email,
                password=None,  # Pas de mot de passe pour auth Firebase
                first_name=first_name,
                last_name=last_name,
                is_active=True,  # Les utilisateurs Firebase sont actifs par défaut
                is_verified=True  # On suppose que l'email Firebase est vérifié
            )
            
            # Note: Nous n'avons pas besoin de créer un profil car un signal le fait déjà
            # automatiquement lors de la création de l'utilisateur
                
            return user, True

    @staticmethod
    def refresh_token(refresh_token):
        """
        Rafraîchit un token d'accès.
        
        Args:
            refresh_token (str): Token de rafraîchissement
            
        Returns:
            tuple: (access_token, refresh_token)
            
        Raises:
            TokenError: Si le token est invalide ou expiré
        """
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            # Générer un nouveau refresh token
            refresh.set_exp(lifetime=timedelta(days=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].days))
            new_refresh_token = str(refresh)
            
            return access_token, new_refresh_token
        
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement du token: {str(e)}")
            raise TokenError()
    
    @staticmethod
    def change_password(user, current_password, new_password):
        """
        Change le mot de passe d'un utilisateur.
        
        Args:
            user (User): Utilisateur
            current_password (str): Mot de passe actuel
            new_password (str): Nouveau mot de passe
            
        Returns:
            bool: True si le changement a réussi
            
        Raises:
            InvalidCredentialsError: Si le mot de passe actuel est incorrect
        """
        if not user.check_password(current_password):
            raise InvalidCredentialsError("Mot de passe actuel incorrect.")
        
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return True 