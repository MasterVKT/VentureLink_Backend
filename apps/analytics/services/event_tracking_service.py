"""
Service pour le suivi des événements dans l'application.
"""
import logging
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.analytics.models import EventLog, ReferralTracker

logger = logging.getLogger(__name__)


class EventTrackingService:
    """
    Service pour suivre et enregistrer les événements dans l'application.
    """
    
    @staticmethod
    def track_event(
            event_type, 
            user=None, 
            related_object=None,
            metadata=None, 
            ip_address=None, 
            user_agent=None
        ):
        """
        Enregistre un événement dans le journal.
        
        Args:
            event_type: Type d'événement (utilisez EventLog.EventType)
            user: Utilisateur concerné (optionnel)
            related_object: Objet concerné (optionnel)
            metadata: Données supplémentaires (optionnel)
            ip_address: Adresse IP de l'utilisateur (optionnel)
            user_agent: User-Agent du navigateur (optionnel)
            
        Returns:
            EventLog: L'événement enregistré
        """
        try:
            # Préparer les données de contenu si un objet est fourni
            content_type = None
            object_id = None
            
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object.__class__)
                object_id = related_object.id
            
            # Créer l'événement
            event = EventLog.objects.create(
                event_type=event_type,
                user=user,
                content_type=content_type,
                object_id=object_id,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.debug(f"Événement {event_type} enregistré: {event.id}")
            return event
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'événement {event_type}: {str(e)}")
            # Ne pas propager l'erreur pour éviter d'interrompre le flux principal
            return None
    
    @staticmethod
    def track_project_view(project, user=None, ip_address=None, user_agent=None):
        """
        Enregistre une vue de projet.
        
        Args:
            project: Le projet vu
            user: L'utilisateur qui a vu le projet (optionnel)
            ip_address: Adresse IP de l'utilisateur (optionnel)
            user_agent: User-Agent du navigateur (optionnel)
            
        Returns:
            EventLog: L'événement enregistré
        """
        event = EventTrackingService.track_event(
            event_type=EventLog.EventType.PROJECT_VIEW,
            user=user,
            related_object=project,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Importer la fonction ici pour éviter les dépendances circulaires
        from apps.analytics.signals import log_project_view
        log_project_view(project, user, ip_address, user_agent)
        
        return event
    
    @staticmethod
    def track_login(user, ip_address=None, user_agent=None):
        """
        Enregistre une connexion utilisateur.
        
        Args:
            user: L'utilisateur qui s'est connecté
            ip_address: Adresse IP de l'utilisateur (optionnel)
            user_agent: User-Agent du navigateur (optionnel)
            
        Returns:
            EventLog: L'événement enregistré
        """
        event = EventTrackingService.track_event(
            event_type=EventLog.EventType.USER_LOGIN,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Importer la fonction ici pour éviter les dépendances circulaires
        from apps.analytics.signals import log_login
        log_login(user, ip_address, user_agent)
        
        return event
    
    @staticmethod
    def track_referral(
            request, 
            user=None, 
            action=None
        ):
        """
        Enregistre une source de référencement.
        
        Args:
            request: Objet HttpRequest contenant les en-têtes et les paramètres
            user: Utilisateur concerné (optionnel)
            action: Action réalisée (optionnel)
            
        Returns:
            ReferralTracker: L'objet de suivi de référencement créé
        """
        try:
            # Extraire les informations du référent
            referrer = request.META.get('HTTP_REFERER', '')
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Extraire les paramètres UTM
            utm_source = request.GET.get('utm_source', '')
            utm_medium = request.GET.get('utm_medium', '')
            utm_campaign = request.GET.get('utm_campaign', '')
            utm_term = request.GET.get('utm_term', '')
            utm_content = request.GET.get('utm_content', '')
            
            # Déterminer la source
            source = utm_source
            if not source and referrer:
                # Extraire le domaine du référent si possible
                from urllib.parse import urlparse
                try:
                    parsed_referrer = urlparse(referrer)
                    source = parsed_referrer.netloc
                except:
                    source = 'unknown'
            
            # Créer l'enregistrement de référencement
            referral = ReferralTracker.objects.create(
                source=source,
                referrer=referrer,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_term=utm_term,
                utm_content=utm_content,
                user=user,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.debug(f"Référencement enregistré: {referral.id} (source: {source})")
            return referral
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du référencement: {str(e)}")
            return None 