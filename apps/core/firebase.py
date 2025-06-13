"""
Module for Firebase integration.
"""
import logging
import os
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging, firestore

logger = logging.getLogger(__name__)

_firebase_app = None
_firebase_enabled = True


def is_firebase_enabled():
    """
    Check if Firebase should be enabled based on configuration.
    
    Returns:
        bool: True if Firebase should be enabled
    """
    global _firebase_enabled
    
    # Check if explicitly disabled
    if hasattr(settings, 'FIREBASE_ENABLED') and not settings.FIREBASE_ENABLED:
        return False
    
    # Check if we have required configuration
    if hasattr(settings, 'FIREBASE_CONFIG'):
        config = settings.FIREBASE_CONFIG
        return bool(config.get('projectId') and config.get('projectId') != '')
    
    return False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    global _firebase_app, _firebase_enabled
    
    if _firebase_app:
        return True
    
    if not is_firebase_enabled():
        logger.debug("Firebase is disabled or not configured, skipping initialization")
        _firebase_enabled = False
        return False
    
    try:
        # Try to get credentials path from settings
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if not cred_path or not os.path.exists(cred_path):
            # Fallback to config folder
            cred_path = os.path.join(settings.BASE_DIR, 'config/firebase-admin-sdk.json')
        
        if not os.path.exists(cred_path):
            logger.warning("Firebase credentials file not found, Firebase features will be disabled")
            _firebase_enabled = False
            return False
        
        # Check if file contains valid JSON (not placeholder)
        with open(cred_path, 'r') as f:
            content = f.read()
            if 'placeholder' in content.lower() or 'firebase-private-key-placeholder' in content:
                logger.debug("Firebase credentials file contains placeholders, skipping initialization")
                _firebase_enabled = False
                return False
        
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        # Only log as warning in development, error in production
        if settings.DEBUG:
            logger.debug(f"Firebase initialization skipped in development: {str(e)}")
        else:
            logger.error(f"Firebase initialization failed: {str(e)}")
        _firebase_enabled = False
        return False


def get_firestore_client():
    """
    Get a Firestore client instance.
    
    Returns:
        firestore.Client: Firestore client or None if not initialized
    """
    if not _firebase_enabled:
        return None
        
    if not _firebase_app:
        if not initialize_firebase():
            return None
    
    try:
        return firestore.client()
    except Exception as e:
        logger.error(f"Error getting Firestore client: {str(e)}")
        return None


def send_push_notification(token, title, body, data=None):
    """
    Send a push notification to a device.
    
    Args:
        token (str): FCM token of the target device
        title (str): Notification title
        body (str): Notification body
        data (dict, optional): Additional data payload
        
    Returns:
        str: Message ID if successful, None otherwise
    """
    if not _firebase_enabled:
        logger.debug("Firebase disabled, skipping push notification")
        return None
        
    if not _firebase_app:
        if not initialize_firebase():
            return None
    
    try:
        # Create the message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=token
        )
        
        # Send the message
        response = messaging.send(message)
        logger.info(f"Push notification sent successfully: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return None 