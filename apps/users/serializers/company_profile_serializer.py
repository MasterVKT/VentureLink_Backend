from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.users.models import CompanyProfile, CompanyMember
from apps.users.serializers.user_serializer import UserSimpleSerializer


class CompanyProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil d'entreprise.
    """
    logo_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    is_startup = serializers.ReadOnlyField()
    is_mature_company = serializers.ReadOnlyField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'company_name', 'legal_name', 'registration_number', 'vat_number',
            'legal_form', 'logo', 'logo_url', 'description', 'mission_statement',
            'industry', 'specialties', 'company_size', 'employee_count',
            'company_stage', 'founded_year', 'headquarters_address', 'website',
            'linkedin_company', 'twitter_company', 'facebook_company',
            'annual_revenue', 'funding_stage', 'total_funding', 'is_verified',
            'display_name', 'is_startup', 'is_mature_company', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
    
    def get_logo_url(self, obj):
        """
        Retourne l'URL complète du logo.
        """
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_display_name(self, obj):
        """
        Retourne le nom d'affichage de l'entreprise.
        """
        return obj.get_display_name()
    
    def get_member_count(self, obj):
        """
        Retourne le nombre de membres actifs.
        """
        return obj.members.filter(status='ACTIVE').count()


class CompanyProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour du profil d'entreprise.
    """
    class Meta:
        model = CompanyProfile
        fields = [
            'company_name', 'legal_name', 'registration_number', 'vat_number',
            'legal_form', 'logo', 'description', 'mission_statement',
            'industry', 'specialties', 'company_size', 'employee_count',
            'company_stage', 'founded_year', 'headquarters_address', 'website',
            'linkedin_company', 'twitter_company', 'facebook_company',
            'annual_revenue', 'funding_stage', 'total_funding'
        ]
    
    def validate_company_name(self, value):
        """
        Valide le nom de l'entreprise.
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError(_('Le nom de l\'entreprise doit contenir au moins 2 caractères.'))
        return value.strip()
    
    def validate_founded_year(self, value):
        """
        Valide l'année de création.
        """
        if value and value > 2030:
            raise serializers.ValidationError(_('L\'année de création ne peut pas être dans le futur.'))
        return value


class CompanyProfileCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'un profil d'entreprise.
    """
    class Meta:
        model = CompanyProfile
        fields = [
            'company_name', 'legal_name', 'registration_number', 'vat_number',
            'legal_form', 'description', 'mission_statement', 'industry',
            'specialties', 'company_size', 'employee_count', 'company_stage',
            'founded_year', 'headquarters_address', 'website'
        ]
    
    def validate_company_name(self, value):
        """
        Valide le nom de l'entreprise.
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError(_('Le nom de l\'entreprise doit contenir au moins 2 caractères.'))
        return value.strip()
    
    def create(self, validated_data):
        """
        Crée un profil d'entreprise et l'associe à l'utilisateur.
        """
        user = self.context['request'].user
        
        if user.account_type != 'BUSINESS':
            raise serializers.ValidationError(_('Seuls les comptes entreprise peuvent créer un profil d\'entreprise.'))
        
        if hasattr(user, 'company_profile'):
            raise serializers.ValidationError(_('Ce compte possède déjà un profil d\'entreprise.'))
        
        validated_data['user'] = user
        company_profile = CompanyProfile.objects.create(**validated_data)
        
        # Créer automatiquement un membre admin pour le créateur
        CompanyMember.objects.create(
            company_profile=company_profile,
            user=user,
            role='CEO',
            status='ACTIVE',
            is_admin=True
        )
        
        return company_profile


class CompanyMemberSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les membres d'entreprise.
    """
    user = UserSimpleSerializer(read_only=True)
    display_title = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyMember
        fields = [
            'id', 'user', 'role', 'title', 'display_title', 'status',
            'start_date', 'end_date', 'is_admin', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_display_title(self, obj):
        """
        Retourne le titre d'affichage.
        """
        return obj.get_display_title()


class CompanyMemberUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour des membres d'entreprise.
    """
    class Meta:
        model = CompanyMember
        fields = ['role', 'title', 'status', 'start_date', 'end_date', 'is_admin']
    
    def validate(self, data):
        """
        Validation personnalisée.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': _('La date de fin doit être postérieure à la date de début.')
            })
        
        return data


class CompanyProfileSimpleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour le profil d'entreprise.
    Utilisé dans les références d'autres modèles.
    """
    logo_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyProfile
        fields = ['id', 'company_name', 'display_name', 'logo_url', 'industry', 'company_stage']
        read_only_fields = fields
    
    def get_logo_url(self, obj):
        """
        Retourne l'URL complète du logo.
        """
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_display_name(self, obj):
        """
        Retourne le nom d'affichage de l'entreprise.
        """
        return obj.get_display_name() 