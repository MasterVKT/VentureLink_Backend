from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models.profile import (
    Profile, DomainExpertise, ProjectInterest, 
    Education, Experience, Badge, UserBadge
)
from ..validators import (
    validate_education_dates, validate_experience_dates
)


class DomainExpertiseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les domaines d'expertise.
    """
    class Meta:
        model = DomainExpertise
        fields = ['id', 'name', 'years_experience', 'level']
        
    def validate_years_experience(self, value):
        """
        Validation personnalisée pour les années d'expérience.
        """
        if value is not None and value < 0:
            raise serializers.ValidationError(
                _("Les années d'expérience ne peuvent pas être négatives.")
            )
        return value


class ProjectInterestSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les centres d'intérêt.
    """
    class Meta:
        model = ProjectInterest
        fields = ['id', 'name', 'level']


class EducationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les formations.
    """
    class Meta:
        model = Education
        fields = [
            'id', 'institution', 'degree', 'field_of_study',
            'start_year', 'end_year', 'description'
        ]
        
    def validate(self, data):
        """
        Validation personnalisée pour les dates de formation.
        """
        start_year = data.get('start_year')
        end_year = data.get('end_year')
        
        if start_year and end_year:
            try:
                validate_education_dates(start_year, end_year)
            except Exception as e:
                raise serializers.ValidationError(str(e))
                
        return data


class ExperienceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les expériences professionnelles.
    """
    class Meta:
        model = Experience
        fields = [
            'id', 'company', 'title', 'location',
            'current', 'start_date', 'end_date', 'description'
        ]
        
    def validate(self, data):
        """
        Validation personnalisée pour les dates d'expérience.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        current = data.get('current', False)
        
        try:
            validate_experience_dates(start_date, end_date, current)
        except Exception as e:
            raise serializers.ValidationError(str(e))
            
        return data


class BadgeSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les badges.
    """
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'badge_type', 'color', 'icon']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les profils utilisateurs.
    """
    domain_expertise = DomainExpertiseSerializer(many=True, read_only=True)
    project_interests = ProjectInterestSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    badges = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'profile_picture', 'cover_picture', 'bio_short', 'title',
            'website', 'social_linkedin', 'social_twitter', 'social_facebook',
            'domain_expertise', 'project_interests', 'education', 'experience',
            'badges', 'avg_rating', 'rating_count', 'views_count',
            'verification_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'avg_rating', 'rating_count', 'views_count', 'verification_level', 'created_at', 'updated_at']
    
    def get_badges(self, obj):
        """
        Récupère les badges de l'utilisateur.
        """
        user_badges = UserBadge.objects.filter(profile=obj)
        badges = [user_badge.badge for user_badge in user_badges]
        return BadgeSerializer(badges, many=True).data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour du profil.
    """
    class Meta:
        model = Profile
        fields = [
            'bio_short', 'title', 'website',
            'social_linkedin', 'social_twitter', 'social_facebook'
        ]
        
    def validate_website(self, value):
        """
        Validation personnalisée pour le site web.
        """
        if value and not (value.startswith('http://') or value.startswith('https://')):
            return f'https://{value}'
        return value


class ProfilePictureSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de la photo de profil.
    """
    class Meta:
        model = Profile
        fields = ['profile_picture']
        
    def validate_profile_picture(self, value):
        """
        Validation personnalisée pour la photo de profil.
        """
        if value:
            # Vérifier la taille du fichier (max 5 MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    _("La taille de l'image ne doit pas dépasser 5 MB.")
                )
                
            # Vérifier le type de fichier
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError(
                    _("Le fichier doit être une image.")
                )
                
        return value


class CoverPictureSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de l'image de couverture.
    """
    class Meta:
        model = Profile
        fields = ['cover_picture']
        
    def validate_cover_picture(self, value):
        """
        Validation personnalisée pour l'image de couverture.
        """
        if value:
            # Vérifier la taille du fichier (max 10 MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    _("La taille de l'image ne doit pas dépasser 10 MB.")
                )
                
            # Vérifier le type de fichier
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError(
                    _("Le fichier doit être une image.")
                )
                
        return value


class DomainExpertiseCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une expertise.
    """
    class Meta:
        model = DomainExpertise
        fields = ['name', 'years_experience', 'level']
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        return DomainExpertise.objects.create(profile=profile, **validated_data)


class ProjectInterestCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'un centre d'intérêt.
    """
    class Meta:
        model = ProjectInterest
        fields = ['name', 'level']
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        return ProjectInterest.objects.create(profile=profile, **validated_data)


class EducationCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création/mise à jour d'une formation.
    """
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_year', 'end_year', 'description']
    
    def validate(self, data):
        """
        Validation personnalisée pour les dates de formation.
        """
        start_year = data.get('start_year')
        end_year = data.get('end_year')
        
        if start_year and end_year:
            try:
                validate_education_dates(start_year, end_year)
            except Exception as e:
                raise serializers.ValidationError(str(e))
                
        return data
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        return Education.objects.create(profile=profile, **validated_data)


class ExperienceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création/mise à jour d'une expérience.
    """
    class Meta:
        model = Experience
        fields = ['company', 'title', 'location', 'current', 'start_date', 'end_date', 'description']
    
    def validate(self, data):
        """
        Validation personnalisée pour les dates d'expérience.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        current = data.get('current', False)
        
        try:
            validate_experience_dates(start_date, end_date, current)
        except Exception as e:
            raise serializers.ValidationError(str(e))
            
        return data
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        return Experience.objects.create(profile=profile, **validated_data) 