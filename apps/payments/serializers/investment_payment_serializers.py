"""
Serializers pour l'initiation de paiement d'investissement (Tâche B3.2).
"""
import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.investments.models import Investment


class InitiateInvestmentPaymentSerializer(serializers.Serializer):
    """
    Serializer pour initier un paiement d'investissement via My-CoolPay.

    Valide :
    - investment_id : UUID de l'investissement appartenant à l'utilisateur
    - phone_number  : numéro de téléphone au format international (+237...)
    - currency      : devise du paiement (XAF par défaut)
    """

    investment_id = serializers.UUIDField(
        required=True,
        help_text=_("UUID de l'investissement à payer"),
    )
    phone_number = serializers.CharField(
        required=True,
        max_length=20,
        help_text=_("Numéro de téléphone au format international (ex: +237690000000)"),
    )
    currency = serializers.ChoiceField(
        choices=['XAF', 'EUR', 'USD'],
        default='XAF',
        required=False,
        help_text=_("Devise du paiement (XAF, EUR ou USD)"),
    )

    def validate_phone_number(self, value: str) -> str:
        """
        Valider et normaliser le numéro de téléphone.

        Règles :
        - Doit commencer par + (format international)
        - Minimum 10 caractères (+ et 9 chiffres)
        - Uniquement chiffres, +, espaces et tirets
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                _("Le numéro de téléphone est requis.")
            )

        # Normaliser : ajouter +237 si pas de préfixe international
        if not value.startswith('+'):
            value = f'+237{value}'

        # Vérifier le format : + suivi de chiffres, espaces ou tirets (9 à 18 caractères)
        if not re.match(r'^\+[\d\s\-]{9,18}$', value):
            raise serializers.ValidationError(
                _("Format invalide. Utilisez le format international : +237690000000")
            )

        # Vérifier la longueur minimale (+ et au moins 9 chiffres)
        digits_only = re.sub(r'[\s\-]', '', value[1:])
        if len(digits_only) < 9:
            raise serializers.ValidationError(
                _("Numéro de téléphone trop court (minimum 9 chiffres).")
            )

        return value

    def validate_investment_id(self, value) -> object:
        """
        Vérifier que l'investissement existe et appartient à l'utilisateur.

        Règles :
        - L'investissement doit exister
        - L'investissement doit appartenir à l'utilisateur connecté
        - L'investissement ne doit pas être déjà payé (COMPLETED)
        - L'investissement ne doit pas être annulé ou rejeté
        """
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError(_("Utilisateur non authentifié."))

        try:
            investment = Investment.objects.select_related(
                'project', 'investor'
            ).get(id=value, investor=request.user)
        except Investment.DoesNotExist:
            raise serializers.ValidationError(
                _("Investissement introuvable ou vous n'êtes pas l'investisseur.")
            )

        # Vérifier le statut
        if investment.status == Investment.STATUS_COMPLETED:
            raise serializers.ValidationError(
                _("Cet investissement a déjà été payé.")
            )

        if investment.status in [Investment.STATUS_CANCELLED, Investment.STATUS_REJECTED]:
            raise serializers.ValidationError(
                _("Cet investissement est annulé ou rejeté — paiement impossible.")
            )

        # Stocker l'objet pour éviter une deuxième requête dans la vue
        self._investment = investment
        return value

    def get_investment(self) -> Investment:
        """Retourner l'objet Investment validé (évite une requête DB supplémentaire)."""
        return getattr(self, '_investment', None)


class InvestmentPaymentResponseSerializer(serializers.Serializer):
    """
    Serializer de réponse pour l'initiation d'un paiement d'investissement.
    Utilisé uniquement pour la documentation Swagger.
    """
    payment_id = serializers.UUIDField(help_text="ID du paiement créé")
    payment_url = serializers.URLField(
        help_text="URL My-CoolPay vers laquelle rediriger l'utilisateur"
    )
    transaction_ref = serializers.CharField(
        help_text="Référence de transaction My-CoolPay"
    )
    investment_id = serializers.UUIDField(help_text="ID de l'investissement")
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField(help_text="Statut du paiement (PENDING)")
    expires_at = serializers.DateTimeField(
        help_text="Expiration du lien de paiement (1 heure)"
    )
    message = serializers.CharField()
