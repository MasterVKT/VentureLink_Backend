"""
Middleware personnalisés pour l'application VentureLink.
"""
import json
import logging
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed

from apps.core.services.currency_service import CurrencyService
from apps.core.utils.firebase import verify_firebase_token

logger = logging.getLogger(__name__)
User = get_user_model()


class FirebaseAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware pour authentifier les utilisateurs via Firebase JWT.
    
    Ce middleware intercepte les requêtes avec un token Firebase dans l'en-tête
    'Authorization' et authentifie l'utilisateur si le token est valide.
    """
    
    def process_request(self, request):
        """
        Traite la requête et authentifie l'utilisateur si un token Firebase est présent.
        
        Args:
            request: La requête HTTP
        """
        # Si l'utilisateur est déjà authentifié, ne rien faire
        if request.user.is_authenticated:
            return
        
        # Vérifier si un token Firebase est présent dans l'en-tête
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Firebase '):
            firebase_token = auth_header.split(' ')[1]
            
            try:
                # Vérifier le token Firebase
                user_info = verify_firebase_token(firebase_token)
                
                if user_info and user_info.get('uid'):
                    # Récupérer l'utilisateur correspondant
                    try:
                        firebase_uid = user_info.get('uid')
                        email = user_info.get('email')
                        
                        # Rechercher l'utilisateur par e-mail
                        if email:
                            user = User.objects.get(email=email)
                            request.user = user
                            request._firebase_user_info = user_info
                            logger.info(f"Utilisateur {email} authentifié via Firebase")
                        else:
                            logger.warning(f"Token Firebase valide mais sans e-mail")
                    except User.DoesNotExist:
                        logger.warning(f"Token Firebase valide mais utilisateur {email} non trouvé")
                        
            except Exception as e:
                logger.error(f"Erreur d'authentification Firebase: {str(e)}")


class CurrencyConversionMiddleware:
    """
    Middleware pour convertir automatiquement les valeurs monétaires dans la devise
    préférée de l'utilisateur.
    
    Ce middleware intercepte les réponses JSON et convertit les valeurs monétaires
    identifiées par un champ 'currency' adjacent à un champ 'amount' (ou similaire)
    dans la devise préférée de l'utilisateur.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.currency_service = CurrencyService()
        self.default_currency = getattr(settings, 'DEFAULT_CURRENCY', 'EUR')
        # Champs monétaires à rechercher dans les réponses JSON
        self.monetary_fields = [
            ('amount', 'currency'),
            ('funding_min', 'funding_currency'),
            ('funding_max', 'funding_currency'),
            ('price', 'currency'),
        ]
    
    def __call__(self, request):
        # Code exécuté pour chaque requête avant que la vue soit appelée
        response = self.get_response(request)
        
        # Code exécuté pour chaque requête après que la vue soit appelée
        return self.process_response(request, response)
    
    def process_response(self, request, response):
        """
        Traite la réponse avant qu'elle ne soit envoyée au client.
        
        Args:
            request: La requête HTTP
            response: La réponse HTTP
            
        Returns:
            response: La réponse HTTP modifiée
        """
        # Vérifier si la réponse est JSON
        if not hasattr(response, 'content') or not response.get('Content-Type', '').startswith('application/json'):
            return response
        
        # Obtenir la devise préférée de l'utilisateur
        user_currency = self.get_user_currency(request)
        
        # Si la devise est la même que la devise par défaut, rien à faire
        if user_currency == self.default_currency:
            return response
        
        try:
            # Décoder le contenu JSON
            content = json.loads(response.content.decode('utf-8'))
            
            # Convertir les valeurs monétaires
            modified_content = self.convert_monetary_values(content, user_currency)
            
            # Si des modifications ont été apportées, mettre à jour le contenu
            if modified_content != content:
                response.content = json.dumps(modified_content).encode('utf-8')
                
        except (json.JSONDecodeError, UnicodeDecodeError):
            # En cas d'erreur, retourner la réponse originale
            pass
        
        return response
    
    def get_user_currency(self, request):
        """
        Obtient la devise préférée de l'utilisateur.
        
        Args:
            request: La requête HTTP
            
        Returns:
            str: Code ISO de la devise préférée
        """
        # Si l'utilisateur est authentifié et a une préférence de devise
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            user_currency = getattr(request.user.profile, 'preferred_currency', None)
            if user_currency:
                return user_currency
        
        # Sinon, essayer de récupérer la devise depuis les paramètres de la requête
        currency_param = request.GET.get('currency')
        if currency_param and len(currency_param) == 3:  # Code ISO de devise à 3 lettres
            return currency_param.upper()
        
        # Sinon, utiliser la devise par défaut
        return self.default_currency
    
    def convert_monetary_values(self, data, target_currency):
        """
        Convertit récursivement les valeurs monétaires dans un dictionnaire ou une liste.
        
        Args:
            data: Dictionnaire ou liste à traiter
            target_currency: Devise cible
            
        Returns:
            dict/list: Les données avec les valeurs converties
        """
        if isinstance(data, dict):
            for amount_field, currency_field in self.monetary_fields:
                if amount_field in data and currency_field in data:
                    source_currency = data[currency_field]
                    amount = data[amount_field]
                    
                    if amount is not None and source_currency != target_currency:
                        # Convertir la valeur
                        data[amount_field] = self.currency_service.convert_currency(
                            amount=amount,
                            from_currency=source_currency,
                            to_currency=target_currency
                        )
                        # Mettre à jour la devise
                        data[currency_field] = target_currency
                        
                        # Ajouter les informations de conversion pour le client
                        data[f'{amount_field}_original'] = amount
                        data[f'{currency_field}_original'] = source_currency
            
            # Traiter récursivement les sous-dictionnaires
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    data[key] = self.convert_monetary_values(value, target_currency)
                    
        elif isinstance(data, list):
            # Traiter récursivement les éléments de la liste
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    data[i] = self.convert_monetary_values(item, target_currency)
                    
        return data


class RequestLoggingMiddleware:
    """
    Middleware pour journaliser les requêtes et les réponses.
    
    Ce middleware enregistre des informations sur chaque requête HTTP,
    comme la méthode, l'URL, les en-têtes, le temps d'exécution et le code de statut.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')
    
    def __call__(self, request):
        # Enregistrer l'heure de début de la requête
        import time
        start_time = time.time()
        
        # Traiter la requête
        response = self.get_response(request)
        
        # Calculer la durée d'exécution
        duration = time.time() - start_time
        
        # Collecter les informations sur la requête
        request_info = {
            'method': request.method,
            'path': request.path,
            'query': request.GET.dict(),
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'ip': self.get_client_ip(request),
            'duration': f"{duration:.3f}s",
            'status': response.status_code,
        }
        
        # Journaliser la requête avec un niveau de log approprié
        if response.status_code >= 500:
            self.logger.error(f"Request: {request_info}")
        elif response.status_code >= 400:
            self.logger.warning(f"Request: {request_info}")
        else:
            self.logger.info(f"Request: {request_info}")
        
        return response
    
    def get_client_ip(self, request):
        """
        Obtient l'adresse IP du client en tenant compte des proxys.
        
        Args:
            request: La requête HTTP
            
        Returns:
            str: L'adresse IP du client
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Récupérer la première IP (celle du client) de la chaîne
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip 