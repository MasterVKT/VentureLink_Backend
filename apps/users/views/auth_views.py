"""
Vues pour l'authentification des utilisateurs.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import jwt
import secrets
import firebase_admin
from firebase_admin import auth as firebase_auth
import requests
import json
import logging

from apps.users.serializers import UserRegistrationSerializer, UserSerializer, BusinessUserRegistrationSerializer
from apps.core.utils.email import send_email_verification, send_password_reset
from apps.core.utils.tokens import generate_token, validate_token
from apps.users.services.auth_service import AuthService
from apps.users.services.user_service import UserService

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Vue pour l'inscription des utilisateurs."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Génération du token d'activation
            send_email_verification(user)
            
            return Response(
                {"message": _("Inscription réussie. Veuillez vérifier votre adresse e-mail pour activer votre compte.")},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BusinessRegisterView(APIView):
    """Vue pour l'inscription des utilisateurs entreprise."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = BusinessUserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Génération du token d'activation
            send_email_verification(user)
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Journaliser l'inscription
            logger.info(f"Nouvelle inscription entreprise: {user.email}")
            
            return Response({
                "message": _("Inscription entreprise réussie. Veuillez vérifier votre adresse e-mail pour activer votre compte."),
                "user": UserSerializer(user).data,
                "access": access_token,
                "refresh": refresh_token,
                "company_profile": {
                    "id": user.company_profile.id,
                    "company_name": user.company_profile.company_name,
                    "industry": user.company_profile.industry,
                    "company_size": user.company_profile.company_size,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Vue pour la déconnexion des utilisateurs."""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": _("Le token de rafraîchissement est requis.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Ajouter le token à la liste noire
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Journaliser la déconnexion
            logger.info(f"Utilisateur {request.user.email} déconnecté avec succès")
            
            return Response(
                {"message": _("Déconnexion réussie.")},
                status=status.HTTP_200_OK
            )
        except TokenError:
            logger.warning(f"Tentative de déconnexion avec un token invalide par {request.user.email}")
            return Response(
                {"error": _("Token de rafraîchissement invalide ou expiré.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion de {request.user.email}: {str(e)}")
            return Response(
                {"error": _("Une erreur est survenue lors de la déconnexion.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FirebaseAuthView(APIView):
    """Vue pour l'authentification via Firebase."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        # Accepter à la fois 'firebase_token' et 'id_token' pour la compatibilité
        id_token = request.data.get('firebase_token') or request.data.get('id_token')
        if not id_token:
            return Response(
                {"error": _("Le token d'identification Firebase est requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Utiliser le service d'authentification
            user, access_token, refresh_token, is_new_user = AuthService.authenticate_with_firebase(id_token)
            
            # Journaliser l'authentification réussie
            logger.info(f"Authentification Firebase réussie pour {user.email}")
            
            # Si c'est un nouvel utilisateur, nous pouvons enrichir son profil
            if is_new_user and 'profile_data' in request.data:
                try:
                    profile_data = request.data.get('profile_data', {})
                    UserService.update_user_profile(user, profile_data)
                    logger.info(f"Profil initial créé pour {user.email}")
                except Exception as e:
                    # Ne pas échouer l'authentification si la mise à jour du profil échoue
                    logger.error(f"Erreur lors de la création du profil: {str(e)}")
            
            # Retourner la réponse avec les tokens et les informations utilisateur
            response_data = {
                "access": access_token,
                "refresh": refresh_token,
                "user": UserSerializer(user).data,
                "is_new_user": is_new_user
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except firebase_admin.exceptions.ExpiredIdTokenError:
            return Response(
                {"error": _("Le token Firebase a expiré. Veuillez vous reconnecter.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except firebase_admin.exceptions.InvalidIdTokenError:
            return Response(
                {"error": _("Le token Firebase est invalide.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except firebase_admin.exceptions.RevokedIdTokenError:
            return Response(
                {"error": _("Le token Firebase a été révoqué. Veuillez vous reconnecter.")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except firebase_admin.exceptions.FirebaseError as e:
            return Response(
                {"error": _("Erreur d'authentification Firebase: {}").format(str(e))},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'authentification Firebase: {str(e)}")
            return Response(
                {"error": _("Une erreur est survenue lors de l'authentification.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleAuthView(APIView):
    """Vue pour l'authentification via Google."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        # Cette vue peut réutiliser la logique de FirebaseAuthView
        # ou implémenter une authentification directe via Google OAuth
        return Response(
            {"message": _("Cette fonctionnalité sera disponible prochainement.")},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class FacebookAuthView(APIView):
    """Vue pour l'authentification via Facebook."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        # Cette vue peut réutiliser la logique de FirebaseAuthView
        # ou implémenter une authentification directe via Facebook OAuth
        return Response(
            {"message": _("Cette fonctionnalité sera disponible prochainement.")},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class PasswordResetView(APIView):
    """Vue pour la demande de réinitialisation de mot de passe."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"error": _("L'adresse e-mail est requise.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            send_password_reset(user)
            
            return Response(
                {"message": _("Instructions de réinitialisation envoyées à votre adresse e-mail.")},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas indiquer si l'e-mail existe
            return Response(
                {"message": _("Si cette adresse e-mail est associée à un compte, des instructions de réinitialisation ont été envoyées.")},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetConfirmView(APIView):
    """Vue pour la confirmation de réinitialisation de mot de passe."""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response(
                {"error": _("Le token et le nouveau mot de passe sont requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validation du token
            user_id = validate_token(token)
            if not user_id:
                return Response(
                    {"error": _("Token invalide ou expiré.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mise à jour du mot de passe
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            
            return Response(
                {"message": _("Mot de passe réinitialisé avec succès.")},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": _("Utilisateur introuvable.")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AccountVerificationView(APIView):
    """Vue pour la vérification du compte utilisateur."""
    permission_classes = (AllowAny,)
    
    def get(self, request, token):
        try:
            # Validation du token
            user_id = validate_token(token)
            if not user_id:
                logger.warning(f"Tentative de vérification avec un token invalide ou expiré: {token}")
                return Response(
                    {"error": _("Token invalide ou expiré.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Activation du compte
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                logger.error(f"Utilisateur introuvable lors de la vérification du compte avec token: {token}")
                return Response(
                    {"error": _("Utilisateur introuvable.")},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            if user.is_verified:
                logger.info(f"Tentative de vérification d'un compte déjà vérifié: {user.email}")
                return Response(
                    {"message": _("Ce compte est déjà vérifié.")},
                    status=status.HTTP_200_OK
                )
            
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            
            # Journaliser la vérification
            logger.info(f"Compte vérifié avec succès: {user.email}")
            
            return Response(
                {"message": _("Compte vérifié avec succès.")},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du compte: {str(e)}")
            return Response(
                {"error": _("Une erreur est survenue lors de la vérification du compte.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailVerificationView(APIView):
    """Vue pour demander un nouvel e-mail de vérification."""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        user = request.user
        
        if user.is_verified:
            logger.info(f"Tentative de vérification d'email pour un compte déjà vérifié: {user.email}")
            return Response(
                {"message": _("Ce compte est déjà vérifié.")},
                status=status.HTTP_200_OK
            )
        
        try:
            # Envoyer l'email de vérification
            send_email_verification(user)
            
            # Journaliser l'envoi
            logger.info(f"E-mail de vérification envoyé à {user.email}")
            
            return Response(
                {"message": _("E-mail de vérification envoyé. Veuillez vérifier votre boîte de réception.")},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'e-mail de vérification à {user.email}: {str(e)}")
            return Response(
                {"error": _("Une erreur est survenue lors de l'envoi de l'e-mail de vérification.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 