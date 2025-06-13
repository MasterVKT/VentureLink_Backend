from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class VentureLinkException(APIException):
    """
    Exception de base pour toutes les exceptions personnalisées VentureLink.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Une erreur s'est produite")
    default_code = 'INTERNAL_SERVER_ERROR'


class AuthenticationError(VentureLinkException):
    """
    Exception levée lors d'une erreur d'authentification.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Authentification échouée")
    default_code = 'AUTHENTICATION_FAILED'


class InvalidCredentialsError(AuthenticationError):
    """
    Exception levée lorsque les identifiants sont invalides.
    """
    default_detail = _("Identifiants invalides")
    default_code = 'INVALID_CREDENTIALS'


class TokenError(AuthenticationError):
    """
    Exception levée lorsqu'un token est invalide ou expiré.
    """
    default_detail = _("Token invalide ou expiré")
    default_code = 'TOKEN_INVALID'


class PermissionDeniedError(VentureLinkException):
    """
    Exception levée lorsque l'utilisateur n'a pas la permission requise.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Vous n'avez pas la permission d'effectuer cette action")
    default_code = 'PERMISSION_DENIED'


class ResourceNotFoundError(VentureLinkException):
    """
    Exception levée lorsqu'une ressource n'est pas trouvée.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Ressource introuvable")
    default_code = 'RESOURCE_NOT_FOUND'


class ValidationError(VentureLinkException):
    """
    Exception levée lors d'une erreur de validation.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Les données fournies sont invalides")
    default_code = 'VALIDATION_ERROR'


class RateLimitExceededError(VentureLinkException):
    """
    Exception levée lorsque la limite de requêtes est dépassée.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Trop de requêtes. Veuillez réessayer plus tard")
    default_code = 'RATE_LIMIT_EXCEEDED'


class SubscriptionRequiredError(VentureLinkException):
    """
    Exception levée lorsqu'un abonnement premium est requis.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Cette fonctionnalité nécessite un abonnement premium")
    default_code = 'SUBSCRIPTION_REQUIRED'


class LimitReachedError(VentureLinkException):
    """
    Exception levée lorsqu'une limite est atteinte.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Vous avez atteint la limite pour cette ressource")
    default_code = 'LIMIT_REACHED'


class ResourceConflictError(VentureLinkException):
    """
    Exception levée lors d'un conflit de ressource.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Conflit avec l'état actuel de la ressource")
    default_code = 'RESOURCE_CONFLICT'


class PaymentError(VentureLinkException):
    """
    Exception levée lors d'une erreur de paiement.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Une erreur s'est produite lors du traitement du paiement")
    default_code = 'PAYMENT_ERROR'


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé qui formate les erreurs selon les standards définis.
    """
    # D'abord, utiliser le gestionnaire d'exceptions par défaut de DRF
    response = exception_handler(exc, context)
    
    # Si le gestionnaire par défaut n'a pas traité l'exception, ou si l'exception n'est pas de DRF
    if response is None:
        return None
    
    # Formater la réponse d'erreur
    error_data = {
        'error': {
            'status_code': response.status_code,
            'error_code': getattr(exc, 'default_code', 'UNKNOWN_ERROR'),
            'message': response.data.get('detail', str(exc)),
        }
    }
    
    # Ajouter les détails si disponibles
    if isinstance(response.data, dict) and 'detail' not in response.data:
        error_details = []
        for field, messages in response.data.items():
            if isinstance(messages, list):
                for message in messages:
                    error_details.append({
                        'field': field,
                        'message': message
                    })
            else:
                error_details.append({
                    'field': field,
                    'message': messages
                })
        
        if error_details:
            error_data['error']['details'] = error_details
    
    response.data = error_data
    return response 