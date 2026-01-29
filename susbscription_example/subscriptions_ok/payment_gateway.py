from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from .services import PaymentService

def validate_amount(amount, service_type, coach=None):
    """
    Valide le mmontant en fonction du type de service
    """
    try:
        amount = Decimal(str(amount))
    except:
        raise ValidationError("Le montant doit être un nombre valide")

    if amount <= 0:
        raise ValidationError("Le montant doit être supérieur à 0")
        
    if service_type == 'coach_subscription' and coach:
        if amount != coach.subscription_price:
            raise ValidationError(f"Le montant ne correspond pas au prix d'abonnement du coach ({coach.subscription_price} XAF)")
            
    return amount

def validate_phone_number(phone):
    """
    Valide le format du numéro de téléphone
    """
    # Supprime les espaces et tirets
    phone = ''.join(filter(str.isdigit, phone))
    
    if not phone or len(phone) < 8:
        raise ValidationError("Numéro de téléphone invalide")
        
    return phone

def initiate_payment(amount, phone, transaction_ref, language='fr', service_type='premium', coach=None):
    """
    Initie un paiement via My-CoolPay avec validations
    """
    try:
        # Validation du montant
        validated_amount = validate_amount(amount, service_type, coach)
        
        # Validation du numéro de téléphone
        validated_phone = validate_phone_number(phone)
        
        # Construction du motif de paiement
        if service_type == 'premium':
            payment_reason = "Abonnement Premium XP Trading"
        else:
            coach_name = coach.user.get_full_name() if coach and hasattr(coach, 'user') else 'Unknown'
            payment_reason = f"Abonnement Coach {coach_name}"
            
        # Utilisation du PaymentService existant avec les paramètres validés
        payment_data, _ = PaymentService.initiate_payment(
            user=None,  # Le PaymentService gère le cas où user est None
            phone_number=validated_phone,
            language=language,
            amount=validated_amount
        )
        
        return payment_data.get('payment_url')
        
    except ValidationError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise Exception(f"Erreur lors de l'initiation du paiement: {str(e)}")