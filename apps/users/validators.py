"""
Validateurs pour les modèles de l'application utilisateurs.
"""
import re
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


# Validation des URLs de réseaux sociaux
linkedin_validator = RegexValidator(
    regex=r'^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w\-\.]+\/?$',
    message=_("Veuillez saisir une URL LinkedIn valide (ex: https://www.linkedin.com/in/username)")
)

twitter_validator = RegexValidator(
    regex=r'^(https?:\/\/)?(www\.)?twitter\.com\/[\w\-\.]+\/?$',
    message=_("Veuillez saisir une URL Twitter valide (ex: https://twitter.com/username)")
)

facebook_validator = RegexValidator(
    regex=r'^(https?:\/\/)?(www\.)?facebook\.com\/[\w\-\.]+\/?$',
    message=_("Veuillez saisir une URL Facebook valide (ex: https://www.facebook.com/username)")
)

# Validation des années d'expérience
min_years_validator = MinValueValidator(
    0, message=_("Les années d'expérience ne peuvent pas être négatives")
)
max_years_validator = MaxValueValidator(
    80, message=_("Les années d'expérience semblent trop élevées")
)

# Validation des années de formation
education_year_validator = RegexValidator(
    regex=r'^(19|20)\d{2}$',
    message=_("Veuillez saisir une année valide au format YYYY (ex: 2023)")
)


def validate_date_format(value):
    """
    Valide le format de date YYYY-MM.
    
    Args:
        value (str): La date à valider
        
    Raises:
        ValidationError: Si le format est incorrect
    """
    if not re.match(r'^(19|20)\d{2}-(0[1-9]|1[0-2])$', value):
        raise ValidationError(
            _("Le format de date doit être YYYY-MM (ex: 2023-01)")
        )


def validate_experience_dates(start_date, end_date, current):
    """
    Valide les dates de début et de fin d'une expérience.
    
    Args:
        start_date (str): Date de début au format YYYY-MM
        end_date (str): Date de fin au format YYYY-MM ou None
        current (bool): Indique si c'est l'expérience actuelle
        
    Raises:
        ValidationError: Si les dates sont incohérentes
    """
    if not start_date:
        raise ValidationError(
            _("La date de début est requise")
        )
    
    # Valider le format des dates
    validate_date_format(start_date)
    
    if end_date and not current:
        validate_date_format(end_date)
        
        # Vérifier que la date de fin est après la date de début
        if end_date < start_date:
            raise ValidationError(
                _("La date de fin doit être postérieure à la date de début")
            )
    
    # Si current est True, end_date devrait être vide
    if current and end_date:
        raise ValidationError(
            _("Une expérience actuelle ne peut pas avoir de date de fin")
        )


def validate_education_dates(start_year, end_year):
    """
    Valide les années de début et de fin d'une formation.
    
    Args:
        start_year (int): Année de début
        end_year (int): Année de fin ou None
        
    Raises:
        ValidationError: Si les années sont incohérentes
    """
    if not start_year:
        raise ValidationError(
            _("L'année de début est requise")
        )
    
    # Si l'année de fin est spécifiée, vérifier qu'elle est après l'année de début
    if end_year is not None and end_year < start_year:
        raise ValidationError(
            _("L'année de fin doit être postérieure à l'année de début")
        )


def validate_color_code(value):
    """
    Valide un code couleur hexadécimal.
    
    Args:
        value (str): Code couleur à valider (ex: #42B72A)
        
    Raises:
        ValidationError: Si le format est incorrect
    """
    if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise ValidationError(
            _("Le code couleur doit être au format hexadécimal (ex: #42B72A)")
        ) 