"""
Vues pour la gestion des utilisateurs et des profils.
"""
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import os

from apps.users.serializers import (
    UserSerializer, UserUpdateSerializer, 
    PasswordChangeSerializer, ProfileSerializer,
    ProfileUpdateSerializer, ProfilePictureSerializer,
    CoverPictureSerializer, DomainExpertiseSerializer,
    DomainExpertiseCreateSerializer, ProjectInterestSerializer,
    ProjectInterestCreateSerializer, EducationSerializer,
    EducationCreateUpdateSerializer, ExperienceSerializer,
    ExperienceCreateUpdateSerializer, BadgeSerializer,
    SubscriptionSerializer, SubscriptionTransactionSerializer,
    SubscriptionUpdateSerializer, SubscriptionCheckoutSerializer
)
from apps.users.models import (
    User, Profile, Subscription, DomainExpertise,
    ProjectInterest, Education, Experience, Badge
)
from apps.core.permissions import IsOwnerOrAdmin, IsAdminUser
from apps.users.services.user_service import UserService
from apps.users.services.profile_service import ProfileService
from apps.users.services.subscription_service import SubscriptionService


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet pour les utilisateurs."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        if self.action == 'change_password':
            return PasswordChangeSerializer
        return UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            # Permettre l'accès via /users/me/
            return self.request.user
        return super().get_object()
    
    def check_permissions(self, request):
        if self.action in ['update', 'partial_update', 'destroy', 'change_password']:
            # Vérifier que l'utilisateur est le propriétaire du compte ou un admin
            obj = self.get_object()
            if obj != request.user and not request.user.is_staff:
                self.permission_denied(request)
        super().check_permissions(request)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Changer le mot de passe de l'utilisateur."""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Vérification et mise à jour du mot de passe
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"message": _("Mot de passe modifié avec succès.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet pour les profils utilisateurs."""
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        if self.action == 'upload_profile_picture':
            return ProfilePictureSerializer
        if self.action == 'upload_cover_picture':
            return CoverPictureSerializer
        return ProfileSerializer
    
    def get_queryset(self):
        """
        Récupère les profils avec leurs relations pour optimiser les requêtes.
        Utilise select_related pour les relations ForeignKey et 
        prefetch_related pour les relations ManyToMany ou reverse ForeignKey.
        """
        queryset = Profile.objects.select_related('user').prefetch_related(
            'domain_expertise',
            'project_interests',
            'education',
            'experience',
            'badges__badge'
        )
        
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
            
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """
        Récupère un profil spécifique et incrémente le compteur de vues.
        """
        instance = self.get_object()
        
        # Incrémenter le compteur de vues seulement si ce n'est pas le propriétaire
        if request.user != instance.user:
            instance.increment_views()
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            # Permettre l'accès via /profiles/me/
            return self.request.user.profile
        return super().get_object()
    
    def check_permissions(self, request):
        if self.action in ['update', 'partial_update', 'upload_profile_picture', 'upload_cover_picture']:
            # Vérifier que l'utilisateur est le propriétaire du profil ou un admin
            obj = self.get_object()
            if obj.user != request.user and not request.user.is_staff:
                self.permission_denied(request)
        super().check_permissions(request)
    
    @action(detail=True, methods=['post'])
    def upload_profile_picture(self, request, pk=None):
        """Télécharger une photo de profil."""
        profile = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Supprimer l'ancienne image si elle existe
            if profile.profile_picture and os.path.isfile(profile.profile_picture.path):
                os.remove(profile.profile_picture.path)
            
            # Sauvegarder la nouvelle image
            profile.profile_picture = serializer.validated_data['profile_picture']
            profile.save()
            
            return Response(
                {"message": _("Photo de profil mise à jour avec succès.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def upload_cover_picture(self, request, pk=None):
        """Télécharger une photo de couverture."""
        profile = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Supprimer l'ancienne image si elle existe
            if profile.cover_picture and os.path.isfile(profile.cover_picture.path):
                os.remove(profile.cover_picture.path)
            
            # Sauvegarder la nouvelle image
            profile.cover_picture = serializer.validated_data['cover_picture']
            profile.save()
            
            return Response(
                {"message": _("Photo de couverture mise à jour avec succès.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def expertise(self, request, pk=None):
        """Obtenir les domaines d'expertise de l'utilisateur."""
        profile = self.get_object()
        expertises = DomainExpertise.objects.filter(profile=profile).select_related('profile')
        serializer = DomainExpertiseSerializer(expertises, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_expertise(self, request, pk=None):
        """Ajouter un domaine d'expertise."""
        profile = self.get_object()
        serializer = DomainExpertiseCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            expertise = serializer.save(profile=profile)
            return Response(
                DomainExpertiseSerializer(expertise).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def interests(self, request, pk=None):
        """Obtenir les centres d'intérêt pour les projets."""
        profile = self.get_object()
        interests = ProjectInterest.objects.filter(profile=profile).select_related('profile')
        serializer = ProjectInterestSerializer(interests, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_interest(self, request, pk=None):
        """Ajouter un centre d'intérêt pour les projets."""
        profile = self.get_object()
        serializer = ProjectInterestCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            interest = serializer.save(profile=profile)
            return Response(
                ProjectInterestSerializer(interest).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def education(self, request, pk=None):
        """Obtenir les formations de l'utilisateur."""
        profile = self.get_object()
        education = Education.objects.filter(profile=profile).select_related('profile')
        serializer = EducationSerializer(education, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_education(self, request, pk=None):
        """Ajouter une formation."""
        profile = self.get_object()
        serializer = EducationCreateUpdateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            education = serializer.save(profile=profile)
            return Response(
                EducationSerializer(education).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def experience(self, request, pk=None):
        """Obtenir les expériences professionnelles de l'utilisateur."""
        profile = self.get_object()
        experience = Experience.objects.filter(profile=profile).select_related('profile')
        serializer = ExperienceSerializer(experience, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_experience(self, request, pk=None):
        """Ajouter une expérience professionnelle."""
        profile = self.get_object()
        serializer = ExperienceCreateUpdateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            experience = serializer.save(profile=profile)
            return Response(
                ExperienceSerializer(experience).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def badges(self, request, pk=None):
        """Obtenir les badges de l'utilisateur."""
        profile = self.get_object()
        badges = Badge.objects.filter(userbadge__profile=profile).select_related()
        serializer = BadgeSerializer(badges, many=True)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les abonnements utilisateurs."""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'checkout':
            return SubscriptionCheckoutSerializer
        if self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def check_permissions(self, request):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Vérifier que l'utilisateur est le propriétaire de l'abonnement ou un admin
            obj = self.get_object()
            if obj.user != request.user and not request.user.is_staff:
                self.permission_denied(request)
        super().check_permissions(request)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Créer un paiement pour un abonnement."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Traitement du paiement via le service d'abonnement
            payment_result = SubscriptionService.process_subscription_payment(
                user=request.user,
                plan_id=serializer.validated_data['plan_id'],
                payment_method=serializer.validated_data['payment_method'],
                payment_details=serializer.validated_data.get('payment_details', {})
            )
            
            if payment_result.get('success'):
                return Response(payment_result, status=status.HTTP_200_OK)
            return Response(payment_result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Obtenir l'historique des transactions d'un abonnement."""
        subscription = self.get_object()
        transactions = subscription.transactions.all()
        serializer = SubscriptionTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler un abonnement."""
        subscription = self.get_object()
        
        if subscription.status == 'CANCELLED':
            return Response(
                {"error": _("Cet abonnement est déjà annulé.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Annuler l'abonnement via le service
        result = SubscriptionService.cancel_subscription(subscription)
        
        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST) 