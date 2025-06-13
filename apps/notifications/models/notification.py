"""
Models for notification management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.core.models import TimeStampedModel, UUIDModel
from apps.users.models import User


class NotificationCategory(models.TextChoices):
    """
    Categories for notifications.
    """
    GENERAL = 'GENERAL', _('Général')
    PROJECT = 'PROJECT', _('Projet')
    INVESTMENT = 'INVESTMENT', _('Investissement')
    MESSAGE = 'MESSAGE', _('Message')
    PAYMENT = 'PAYMENT', _('Paiement')
    SYSTEM = 'SYSTEM', _('Système')


class NotificationPriority(models.TextChoices):
    """
    Priority levels for notifications.
    """
    LOW = 'LOW', _('Basse')
    NORMAL = 'NORMAL', _('Normale')
    HIGH = 'HIGH', _('Élevée')
    URGENT = 'URGENT', _('Urgente')


class NotificationStatus(models.TextChoices):
    """
    Status options for notifications.
    """
    UNREAD = 'UNREAD', _('Non lue')
    READ = 'READ', _('Lue')
    ARCHIVED = 'ARCHIVED', _('Archivée')
    DELETED = 'DELETED', _('Supprimée')


class NotificationDeliveryMethod(models.TextChoices):
    """
    Available delivery methods for notifications.
    """
    APP = 'APP', _('Application')
    EMAIL = 'EMAIL', _('E-mail')
    SMS = 'SMS', _('SMS')
    PUSH = 'PUSH', _('Notification push')


class Notification(UUIDModel, TimeStampedModel):
    """
    Model representing a notification sent to a user.
    """
    # Recipient of the notification
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Destinataire'),
    )
    
    # Notification details
    title = models.CharField(
        _('Titre'),
        max_length=255,
    )
    
    content = models.TextField(
        _('Contenu'),
    )
    
    # Category and priority
    category = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.GENERAL,
    )
    
    priority = models.CharField(
        _('Priorité'),
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    
    # Status and read tracking
    status = models.CharField(
        _('Statut'),
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.UNREAD,
    )
    
    read_at = models.DateTimeField(
        _('Lu le'),
        null=True,
        blank=True,
    )
    
    # Delivery method tracking
    delivery_methods = models.CharField(
        _('Méthodes de livraison'),
        max_length=255,
        help_text=_('Méthodes de livraison séparées par des virgules'),
        default=NotificationDeliveryMethod.APP,
    )
    
    delivered = models.BooleanField(
        _('Livrée'),
        default=False,
    )
    
    # Link to related object (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Type de contenu'),
    )
    
    object_id = models.CharField(
        _('ID de l\'objet'),
        max_length=255,
        null=True,
        blank=True,
    )
    
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional attributes
    action_url = models.CharField(
        _('URL d\'action'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('URL où rediriger l\'utilisateur quand il clique sur la notification'),
    )
    
    icon = models.CharField(
        _('Icône'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Nom de l\'icône à afficher'),
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient}"
    
    def mark_as_read(self):
        """
        Mark the notification as read.
        """
        from django.utils import timezone
        
        if self.status != NotificationStatus.READ:
            self.status = NotificationStatus.READ
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def archive(self):
        """
        Archive the notification.
        """
        if self.status != NotificationStatus.ARCHIVED:
            self.status = NotificationStatus.ARCHIVED
            self.save(update_fields=['status', 'updated_at'])
    
    def delete_notification(self):
        """
        Mark the notification as deleted (soft delete).
        """
        if self.status != NotificationStatus.DELETED:
            self.status = NotificationStatus.DELETED
            self.save(update_fields=['status', 'updated_at'])
    
    def get_delivery_methods_list(self):
        """
        Get a list of delivery methods.
        """
        return self.delivery_methods.split(',')
    
    def set_delivery_methods_list(self, methods):
        """
        Set delivery methods from a list.
        """
        self.delivery_methods = ','.join(methods)


class NotificationTemplate(UUIDModel, TimeStampedModel):
    """
    Model for notification templates that can be reused.
    """
    code = models.CharField(
        _('Code'),
        max_length=100,
        unique=True,
        help_text=_('Code unique pour identifier le modèle'),
    )
    
    name = models.CharField(
        _('Nom'),
        max_length=255,
    )
    
    category = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.GENERAL,
    )
    
    title_template = models.CharField(
        _('Modèle de titre'),
        max_length=255,
        help_text=_('Modèle de titre avec placeholders (ex: "Nouveau message de {sender_name}")'),
    )
    
    content_template = models.TextField(
        _('Modèle de contenu'),
        help_text=_('Modèle de contenu avec placeholders'),
    )
    
    priority = models.CharField(
        _('Priorité'),
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    
    default_icon = models.CharField(
        _('Icône par défaut'),
        max_length=50,
        null=True,
        blank=True,
    )
    
    default_delivery_methods = models.CharField(
        _('Méthodes de livraison par défaut'),
        max_length=255,
        default=NotificationDeliveryMethod.APP,
        help_text=_('Méthodes de livraison séparées par des virgules'),
    )
    
    description = models.TextField(
        _('Description'),
        null=True,
        blank=True,
        help_text=_('Description de l\'utilisation du modèle'),
    )
    
    is_active = models.BooleanField(
        _('Actif'),
        default=True,
        help_text=_('Si désactivé, ce modèle ne sera pas utilisé'),
    )
    
    class Meta:
        verbose_name = _('Modèle de notification')
        verbose_name_plural = _('Modèles de notification')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_delivery_methods_list(self):
        """
        Get a list of default delivery methods.
        """
        return self.default_delivery_methods.split(',')
    
    def set_delivery_methods_list(self, methods):
        """
        Set default delivery methods from a list.
        """
        self.default_delivery_methods = ','.join(methods)


class NotificationUserPreference(UUIDModel, TimeStampedModel):
    """
    Model for user notification preferences.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('Utilisateur'),
    )
    
    enable_email = models.BooleanField(
        _('Activer les emails'),
        default=True,
    )
    
    enable_push = models.BooleanField(
        _('Activer les notifications push'),
        default=True,
    )
    
    enable_sms = models.BooleanField(
        _('Activer les SMS'),
        default=False,
    )
    
    enable_app = models.BooleanField(
        _('Activer les notifications dans l\'application'),
        default=True,
    )
    
    # Specific category preferences
    project_notifications = models.BooleanField(
        _('Notifications de projet'),
        default=True,
    )
    
    investment_notifications = models.BooleanField(
        _('Notifications d\'investissement'),
        default=True,
    )
    
    message_notifications = models.BooleanField(
        _('Notifications de message'),
        default=True,
    )
    
    payment_notifications = models.BooleanField(
        _('Notifications de paiement'),
        default=True,
    )
    
    system_notifications = models.BooleanField(
        _('Notifications système'),
        default=True,
    )
    
    # Additional preferences
    quiet_hours_start = models.TimeField(
        _('Début des heures silencieuses'),
        null=True,
        blank=True,
    )
    
    quiet_hours_end = models.TimeField(
        _('Fin des heures silencieuses'),
        null=True,
        blank=True,
    )
    
    minimum_priority = models.CharField(
        _('Priorité minimale'),
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.LOW,
        help_text=_('Priorité minimale des notifications à recevoir'),
    )
    
    class Meta:
        verbose_name = _('Préférence de notification')
        verbose_name_plural = _('Préférences de notification')
    
    def __str__(self):
        return f"Préférences de {self.user}"
    
    def is_delivery_method_enabled(self, method):
        """
        Check if a specific delivery method is enabled for the user.
        
        Args:
            method (str): One of NotificationDeliveryMethod choices
            
        Returns:
            bool: Whether the method is enabled
        """
        if method == NotificationDeliveryMethod.APP:
            return self.enable_app
        elif method == NotificationDeliveryMethod.EMAIL:
            return self.enable_email
        elif method == NotificationDeliveryMethod.PUSH:
            return self.enable_push
        elif method == NotificationDeliveryMethod.SMS:
            return self.enable_sms
        return False
    
    def is_category_enabled(self, category):
        """
        Check if a specific notification category is enabled for the user.
        
        Args:
            category (str): One of NotificationCategory choices
            
        Returns:
            bool: Whether the category is enabled
        """
        if category == NotificationCategory.PROJECT:
            return self.project_notifications
        elif category == NotificationCategory.INVESTMENT:
            return self.investment_notifications
        elif category == NotificationCategory.MESSAGE:
            return self.message_notifications
        elif category == NotificationCategory.PAYMENT:
            return self.payment_notifications
        elif category == NotificationCategory.SYSTEM:
            return self.system_notifications
        # General is always enabled
        return True 