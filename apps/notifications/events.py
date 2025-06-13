"""
Module pour gérer les événements qui déclenchent des notifications.

Ce module définit les fonctions qui sont appelées en réponse à divers événements
dans l'application pour envoyer des notifications appropriées aux utilisateurs.
"""
from typing import List, Optional, Dict, Any, Union

from django.utils.translation import gettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import NotificationCategory, NotificationDeliveryMethod
from apps.notifications.services import NotificationService
from apps.users.models import User
from apps.messaging.models import Message, Conversation
from apps.projects.models import Project, ProjectComment
from apps.investments.models import Investment, Repayment


def notify_new_message(message: Message) -> None:
    """
    Envoie une notification lorsqu'un nouveau message est reçu.
    
    Args:
        message: Le message reçu
    """
    # Ne pas notifier l'expéditeur du message
    conversation = message.conversation
    recipients = conversation.participants.exclude(id=message.sender.id)
    
    sender_name = f"{message.sender.first_name} {message.sender.last_name}"
    conversation_name = conversation.title or _("Conversation directe")
    
    for recipient in recipients:
        # Vérifier les préférences de notification de l'utilisateur
        # TODO: Ajouter la vérification des préférences
        
        # Créer une notification contextuelle et push
        NotificationService.create_notification(
            recipient=recipient,
            title=_("Nouveau message"),
            content=_(f"{sender_name} vous a envoyé un message dans {conversation_name}"),
            category=NotificationCategory.MESSAGE,
            delivery_methods=[
                NotificationDeliveryMethod.APP,
                NotificationDeliveryMethod.PUSH
            ],
            related_object=message,
            action_url=f"/conversations/{conversation.id}"
        )


def notify_project_comment(comment: ProjectComment) -> None:
    """
    Envoie une notification lorsqu'un commentaire est ajouté à un projet.
    
    Args:
        comment: Le commentaire ajouté
    """
    project = comment.project
    
    # Notifier le créateur du projet si ce n'est pas lui qui a commenté
    if project.creator.id != comment.author.id:
        commenter_name = f"{comment.author.first_name} {comment.author.last_name}"
        
        NotificationService.create_notification(
            recipient=project.creator,
            title=_("Nouveau commentaire sur votre projet"),
            content=_(f"{commenter_name} a commenté votre projet: {project.title}"),
            category=NotificationCategory.PROJECT,
            delivery_methods=[
                NotificationDeliveryMethod.APP,
                NotificationDeliveryMethod.PUSH,
                NotificationDeliveryMethod.EMAIL
            ],
            related_object=comment,
            action_url=f"/projects/{project.id}/comments"
        )


def notify_new_investment(investment: Investment) -> None:
    """
    Envoie une notification lorsqu'un nouvel investissement est effectué.
    
    Args:
        investment: L'investissement effectué
    """
    project = investment.project
    investor = investment.investor
    
    # Notifier le créateur du projet
    investor_name = f"{investor.first_name} {investor.last_name}"
    amount = f"{investment.amount} {investment.currency}"
    
    # Notification au créateur du projet
    NotificationService.create_notification(
        recipient=project.creator,
        title=_("Nouvel investissement reçu !"),
        content=_(f"{investor_name} a investi {amount} dans votre projet: {project.title}"),
        category=NotificationCategory.INVESTMENT,
        priority="HIGH",
        delivery_methods=[
            NotificationDeliveryMethod.APP,
            NotificationDeliveryMethod.PUSH,
            NotificationDeliveryMethod.EMAIL
        ],
        related_object=investment,
        action_url=f"/projects/{project.id}/investments"
    )


def notify_investment_status_change(investment: Investment) -> None:
    """
    Envoie une notification lorsque le statut d'un investissement change.
    
    Args:
        investment: L'investissement dont le statut a changé
    """
    status_messages = {
        'pending': _("en attente de confirmation"),
        'approved': _("approuvé"),
        'rejected': _("refusé"),
        'cancelled': _("annulé"),
        'completed': _("finalisé")
    }
    
    status_text = status_messages.get(investment.status, investment.status)
    project_title = investment.project.title
    amount = f"{investment.amount} {investment.currency}"
    
    # Notifier l'investisseur
    NotificationService.create_notification(
        recipient=investment.investor,
        title=_("Statut de votre investissement mis à jour"),
        content=_(f"Votre investissement de {amount} dans '{project_title}' est maintenant {status_text}"),
        category=NotificationCategory.INVESTMENT,
        delivery_methods=[
            NotificationDeliveryMethod.APP,
            NotificationDeliveryMethod.PUSH,
            NotificationDeliveryMethod.EMAIL
        ],
        related_object=investment,
        action_url=f"/investments/{investment.id}"
    )


def notify_repayment_received(repayment: Repayment) -> None:
    """
    Envoie une notification lorsqu'un remboursement est reçu.
    
    Args:
        repayment: Le remboursement reçu
    """
    investment = repayment.investment
    amount = f"{repayment.amount} {repayment.currency}"
    project_title = investment.project.title
    
    # Notifier l'investisseur
    NotificationService.create_notification(
        recipient=investment.investor,
        title=_("Remboursement reçu"),
        content=_(f"Vous avez reçu un remboursement de {amount} pour votre investissement dans '{project_title}'"),
        category=NotificationCategory.INVESTMENT,
        delivery_methods=[
            NotificationDeliveryMethod.APP,
            NotificationDeliveryMethod.PUSH,
            NotificationDeliveryMethod.EMAIL
        ],
        related_object=repayment,
        action_url=f"/investments/{investment.id}/repayments"
    )


# Connecter les signaux pour déclencher automatiquement les notifications

@receiver(post_save, sender=Message)
def message_created_handler(sender, instance, created, **kwargs):
    """Déclenche une notification quand un nouveau message est créé."""
    if created:
        notify_new_message(instance)


@receiver(post_save, sender=ProjectComment)
def comment_created_handler(sender, instance, created, **kwargs):
    """Déclenche une notification quand un nouveau commentaire est créé."""
    if created:
        notify_project_comment(instance)


@receiver(post_save, sender=Investment)
def investment_handler(sender, instance, created, **kwargs):
    """Déclenche une notification quand un investissement est créé ou modifié."""
    if created:
        notify_new_investment(instance)
    else:
        # Vérifier si le statut a changé (en comparant avec l'instance précédente)
        if hasattr(instance, '_previous_status') and instance._previous_status != instance.status:
            notify_investment_status_change(instance)


@receiver(post_save, sender=Repayment)
def repayment_created_handler(sender, instance, created, **kwargs):
    """Déclenche une notification quand un remboursement est créé."""
    if created and instance.status == 'completed':
        notify_repayment_received(instance) 