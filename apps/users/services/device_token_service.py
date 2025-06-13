"""
Service pour la gestion des tokens d'appareil.
"""
from django.db import transaction
from typing import Optional, Dict, Any, List

from apps.users.models import User, DeviceToken
from apps.core.exceptions import ResourceNotFoundError, ValidationError


class DeviceTokenService:
    """
    Service pour la gestion des tokens d'appareil.
    """
    
    @staticmethod
    def get_user_tokens(user_id: str, active_only: bool = True) -> List[DeviceToken]:
        """
        Récupère les tokens d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            active_only: Si True, ne récupère que les tokens actifs
            
        Returns:
            List[DeviceToken]: Liste des tokens de l'utilisateur
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
        """
        try:
            user = User.objects.get(id=user_id)
            
            tokens = DeviceToken.objects.filter(user=user)
            if active_only:
                tokens = tokens.filter(is_active=True)
                
            return list(tokens)
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
    
    @staticmethod
    def get_token(token_id: str) -> DeviceToken:
        """
        Récupère un token par son ID.
        
        Args:
            token_id: ID du token
            
        Returns:
            DeviceToken: Le token
            
        Raises:
            ResourceNotFoundError: Si le token n'existe pas
        """
        try:
            return DeviceToken.objects.get(id=token_id)
        except DeviceToken.DoesNotExist:
            raise ResourceNotFoundError("Token d'appareil non trouvé")
    
    @staticmethod
    @transaction.atomic
    def register_device(
        user_id: str,
        token: str,
        platform: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> DeviceToken:
        """
        Enregistre ou met à jour un appareil pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            token: Token FCM de l'appareil
            platform: Plateforme de l'appareil (android, ios, web, desktop)
            device_id: ID de l'appareil (optionnel)
            device_name: Nom de l'appareil (optionnel)
            app_version: Version de l'application (optionnel)
            
        Returns:
            DeviceToken: Le token d'appareil créé ou mis à jour
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
            ValidationError: Si les données sont invalides
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Vérifier que la plateforme est valide
            valid_platforms = [choice[0] for choice in DeviceToken.PLATFORM_CHOICES]
            if platform not in valid_platforms:
                raise ValidationError(f"Plateforme invalide. Valeurs autorisées: {', '.join(valid_platforms)}")
            
            # Si un device_id est fourni, on cherche d'abord un token existant pour cet appareil
            if device_id:
                existing_token = DeviceToken.objects.filter(
                    user=user,
                    device_id=device_id
                ).first()
                
                if existing_token:
                    # Mettre à jour le token existant
                    existing_token.token = token
                    existing_token.platform = platform
                    if device_name:
                        existing_token.device_name = device_name
                    if app_version:
                        existing_token.app_version = app_version
                    existing_token.is_active = True
                    existing_token.save()
                    return existing_token
            
            # Si aucun device_id n'est fourni ou si aucun token n'existe pour cet appareil,
            # on cherche un token existant avec le même token FCM
            try:
                existing_token = DeviceToken.objects.get(token=token)
                
                # Si le token appartient à un autre utilisateur, on le désactive
                if existing_token.user != user:
                    existing_token.is_active = False
                    existing_token.save(update_fields=['is_active', 'updated_at'])
                    
                    # Créer un nouveau token pour cet utilisateur
                    return DeviceToken.objects.create(
                        user=user,
                        token=token,
                        platform=platform,
                        device_id=device_id,
                        device_name=device_name,
                        app_version=app_version,
                        is_active=True
                    )
                else:
                    # Mettre à jour le token existant
                    existing_token.platform = platform
                    if device_id and not existing_token.device_id:
                        existing_token.device_id = device_id
                    if device_name:
                        existing_token.device_name = device_name
                    if app_version:
                        existing_token.app_version = app_version
                    existing_token.is_active = True
                    existing_token.save()
                    return existing_token
                    
            except DeviceToken.DoesNotExist:
                # Créer un nouveau token
                return DeviceToken.objects.create(
                    user=user,
                    token=token,
                    platform=platform,
                    device_id=device_id,
                    device_name=device_name,
                    app_version=app_version,
                    is_active=True
                )
                
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé")
    
    @staticmethod
    def deactivate_token(token_id: str, user_id: str) -> bool:
        """
        Désactive un token d'appareil.
        
        Args:
            token_id: ID du token à désactiver
            user_id: ID de l'utilisateur propriétaire du token
            
        Returns:
            bool: True si le token a été désactivé, False sinon
            
        Raises:
            ResourceNotFoundError: Si le token n'existe pas
            ValidationError: Si l'utilisateur n'est pas le propriétaire du token
        """
        try:
            token = DeviceToken.objects.get(id=token_id)
            
            # Vérifier que l'utilisateur est le propriétaire du token
            if str(token.user.id) != user_id:
                raise ValidationError("Vous n'êtes pas autorisé à désactiver ce token")
            
            token.is_active = False
            token.save(update_fields=['is_active', 'updated_at'])
            return True
            
        except DeviceToken.DoesNotExist:
            raise ResourceNotFoundError("Token d'appareil non trouvé")
    
    @staticmethod
    def deactivate_tokens_by_device_id(device_id: str, user_id: str) -> int:
        """
        Désactive tous les tokens associés à un appareil spécifique.
        
        Args:
            device_id: ID de l'appareil
            user_id: ID de l'utilisateur propriétaire des tokens
            
        Returns:
            int: Nombre de tokens désactivés
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
        """
        try:
            user = User.objects.get(id=user_id)
            
            tokens = DeviceToken.objects.filter(
                user=user,
                device_id=device_id,
                is_active=True
            )
            
            count = tokens.count()
            tokens.update(is_active=False)
            return count
            
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé") 