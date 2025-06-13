"""
Utilitaires d'envoi d'emails.
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags


def send_email_verification(user, verification_url):
    """
    Envoie un email de vérification à l'utilisateur.

    Args:
        user: L'utilisateur auquel envoyer l'email
        verification_url: L'URL de vérification
    """
    subject = 'Vérification de compte VentureLink'
    context = {
        'user': user,
        'verification_url': verification_url
    }
    html_message = render_to_string('emails/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )


def send_password_reset(user, reset_url):
    """
    Envoie un email de réinitialisation de mot de passe à l'utilisateur.

    Args:
        user: L'utilisateur auquel envoyer l'email
        reset_url: L'URL de réinitialisation
    """
    subject = 'Réinitialisation de mot de passe VentureLink'
    context = {
        'user': user,
        'reset_url': reset_url
    }
    html_message = render_to_string('emails/password_reset_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    ) 