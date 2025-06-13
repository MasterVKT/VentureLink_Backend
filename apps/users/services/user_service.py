from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.exceptions import ResourceNotFoundError, ValidationError

User = get_user_model()


class UserService:
    """
    Service pour gérer les opérations liées aux utilisateurs.
    """
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Récupère un utilisateur par son ID.
        
        Args:
            user_id (uuid): ID de l'utilisateur
            
        Returns:
            User: L'utilisateur
            
        Raises:
            ResourceNotFoundError: Si l'utilisateur n'existe pas
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundError("Utilisateur non trouvé.")
    
    @staticmethod
    def update_user(user, data):
        """
        Met à jour les informations d'un utilisateur.
        
        Args:
            user (User): Utilisateur à mettre à jour
            data (dict): Nouvelles données
            
        Returns:
            User: L'utilisateur mis à jour
        """
        for field, value in data.items():
            setattr(user, field, value)
        
        user.save()
        return user
    
    @staticmethod
    def update_fcm_token(user, fcm_token):
        """
        Met à jour le token FCM d'un utilisateur.
        
        Args:
            user (User): Utilisateur
            fcm_token (str): Nouveau token FCM
            
        Returns:
            User: L'utilisateur mis à jour
        """
        user.fcm_token = fcm_token
        user.save(update_fields=['fcm_token'])
        return user
    
    @staticmethod
    def update_preferred_currency(user, currency):
        """
        Met à jour la devise préférée d'un utilisateur.
        
        Args:
            user (User): Utilisateur
            currency (str): Code de la devise
            
        Returns:
            User: L'utilisateur mis à jour
            
        Raises:
            ValidationError: Si la devise n'est pas supportée
        """
        from django.conf import settings
        
        currencies = getattr(settings, 'CURRENCIES', ('EUR', 'USD', 'GBP'))
        
        if currency not in currencies:
            raise ValidationError(f"Devise non supportée. Les devises supportées sont: {', '.join(currencies)}")
        
        user.preferred_currency = currency
        user.save(update_fields=['preferred_currency'])
        return user 