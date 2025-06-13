from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour le modèle User.
    Utilisé pour les références dans d'autres modèles.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'user_type']
        read_only_fields = ['id', 'email', 'full_name', 'user_type']
    
    def get_full_name(self, obj):
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.email


class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle User.
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'user_type',
            'phone_number', 'location', 'language', 'preferred_currency',
            'is_verified', 'is_premium', 'fcm_token', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'is_premium', 'date_joined']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour des informations de l'utilisateur.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'location', 'language', 'preferred_currency', 'fcm_token'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Sérialiseur pour le changement de mot de passe.
    """
    current_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        min_length=8
    )
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Mot de passe actuel incorrect.'))
        return value
    
    def validate_new_password(self, value):
        # Vous pouvez ajouter des validations supplémentaires ici
        if len(value) < 8:
            raise serializers.ValidationError(_('Le mot de passe doit contenir au moins 8 caractères.'))
        
        # Vérifier si le mot de passe contient au moins un chiffre
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(_('Le mot de passe doit contenir au moins un chiffre.'))
        
        # Vérifier si le mot de passe contient au moins une lettre majuscule
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(_('Le mot de passe doit contenir au moins une lettre majuscule.'))
        
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription des utilisateurs.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    terms_accepted = serializers.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'user_type',
            'password', 'password_confirmation', 'terms_accepted'
        ]
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('Un utilisateur avec cette adresse email existe déjà.'))
        return value
    
    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError(_('Vous devez accepter les conditions d\'utilisation.'))
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({'password_confirmation': _('Les mots de passe ne correspondent pas.')})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        validated_data.pop('terms_accepted')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'BOTH')
        )
        
        return user 