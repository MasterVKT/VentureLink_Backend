from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.users.models import CompanyProfile, CompanyMember
from apps.users.serializers.company_profile_serializer import (
    CompanyProfileSerializer, CompanyProfileUpdateSerializer,
    CompanyProfileCreateSerializer, CompanyMemberSerializer,
    CompanyMemberUpdateSerializer, CompanyProfileSimpleSerializer
)


class CompanyProfileViewSet(ModelViewSet):
    """
    ViewSet pour gérer les profils d'entreprise.
    """
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CompanyProfileUpdateSerializer
        elif self.action == 'list':
            return CompanyProfileSimpleSerializer
        return CompanyProfileSerializer
    
    def get_queryset(self):
        return CompanyProfile.objects.all()
    
    def create(self, request, *args, **kwargs):
        """
        Crée un profil d'entreprise pour l'utilisateur connecté.
        """
        if hasattr(request.user, 'company_profile'):
            return Response(
                {'error': _('Ce compte possède déjà un profil d\'entreprise.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_profile = serializer.save()
        
        response_serializer = CompanyProfileSerializer(
            company_profile, 
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='my-company')
    def my_company(self, request):
        """
        Retourne le profil d'entreprise de l'utilisateur connecté.
        """
        if not hasattr(request.user, 'company_profile'):
            return Response(
                {'error': _('Aucun profil d\'entreprise trouvé pour cet utilisateur.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(request.user.company_profile)
        return Response(serializer.data)


class MyCompanyProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et modifier le profil d'entreprise de l'utilisateur connecté.
    """
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CompanyProfileUpdateSerializer
        return CompanyProfileSerializer
    
    def get_object(self):
        if not hasattr(self.request.user, 'company_profile'):
            from django.http import Http404
            raise Http404(_('Aucun profil d\'entreprise trouvé.'))
        return self.request.user.company_profile


class CompanyListView(generics.ListAPIView):
    """
    Vue pour lister les entreprises publiques/vérifiées.
    """
    serializer_class = CompanyProfileSimpleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CompanyProfile.objects.filter(is_verified=True)
        
        # Filtrage par industrie
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        
        # Filtrage par taille d'entreprise
        company_size = self.request.query_params.get('company_size')
        if company_size:
            queryset = queryset.filter(company_size=company_size)
        
        # Filtrage par stade d'entreprise
        company_stage = self.request.query_params.get('company_stage')
        if company_stage:
            queryset = queryset.filter(company_stage=company_stage)
        
        return queryset.order_by('company_name') 