"""
Views for investment management.
"""
from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.investments.models import Investment, InvestmentHistory, InvestmentPayment
from apps.investments.serializers import (
    InvestmentSerializer, InvestmentListSerializer, InvestmentCreateSerializer,
    InvestmentUpdateSerializer, InvestmentStatusUpdateSerializer,
    InvestmentPaymentSerializer, InvestmentPaymentCreateSerializer,
    InvestmentHistorySerializer
)
from apps.investments.services import InvestmentService
from apps.core.permissions import IsAdminUser, IsInvestorOrProjectCreator


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for investments.
    """
    permission_classes = [IsAuthenticated, IsInvestorOrProjectCreator]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'investment_type']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return investments filtered by permissions."""
        user = self.request.user
        
        if self.request.user.is_staff:
            # Admin can see all investments
            return Investment.objects.all()
        
        # Filter by project_id if provided
        project_id = self.request.query_params.get('project_id')
        status = self.request.query_params.get('status')
        investment_type = self.request.query_params.get('investment_type')
        
        return InvestmentService.get_investments(
            user=user,
            project_id=project_id,
            status=status,
            investment_type=investment_type
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return InvestmentListSerializer
        elif self.action == 'create':
            return InvestmentCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return InvestmentUpdateSerializer
        elif self.action == 'update_status':
            return InvestmentStatusUpdateSerializer
        return InvestmentSerializer
    
    def perform_create(self, serializer):
        """Create investment with current user as investor."""
        # Extract data from serializer
        project_id = serializer.validated_data.get('project_id')
        amount = serializer.validated_data.get('amount')
        currency = serializer.validated_data.get('currency')
        investment_type = serializer.validated_data.get('investment_type')
        equity_percentage = serializer.validated_data.get('equity_percentage')
        interest_rate = serializer.validated_data.get('interest_rate')
        term_months = serializer.validated_data.get('term_months')
        description = serializer.validated_data.get('description')
        
        # Create investment
        investment = InvestmentService.create_investment(
            user=self.request.user,
            project_id=project_id,
            amount=amount,
            currency=currency,
            investment_type=investment_type,
            equity_percentage=equity_percentage,
            interest_rate=interest_rate,
            term_months=term_months,
            description=description
        )
        
        # Save investment to serializer
        serializer.instance = investment
    
    def perform_update(self, serializer):
        """Update investment using service."""
        investment_id = self.kwargs.get('pk')
        
        # Update investment
        investment = InvestmentService.update_investment(
            investment_id=investment_id,
            user=self.request.user,
            data=serializer.validated_data
        )
        
        # Save investment to serializer
        serializer.instance = investment
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update investment status.
        Project creators can approve/reject investments.
        """
        investment_id = pk
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        # Update status
        investment = InvestmentService.update_investment_status(
            investment_id=investment_id,
            user=request.user,
            new_status=new_status,
            comment=comment
        )
        
        # Return updated investment
        serializer = self.get_serializer(investment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get investment history."""
        investment = self.get_object()
        history = InvestmentHistory.objects.filter(investment=investment)
        serializer = InvestmentHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get investment payments."""
        investment = self.get_object()
        payments = InvestmentPayment.objects.filter(investment=investment)
        serializer = InvestmentPaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_payment(self, request, pk=None):
        """Create payment for investment."""
        investment = self.get_object()
        serializer = InvestmentPaymentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract data from serializer
            amount = serializer.validated_data.get('amount')
            currency = serializer.validated_data.get('currency')
            payment_method = serializer.validated_data.get('payment_method')
            transaction_id = serializer.validated_data.get('transaction_id')
            payment_details = serializer.validated_data.get('payment_details')
            receipt_file = serializer.validated_data.get('receipt_file')
            notes = serializer.validated_data.get('notes')
            
            # Create payment
            payment = InvestmentService.create_payment(
                investment_id=investment.id,
                user=request.user,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                transaction_id=transaction_id,
                payment_details=payment_details,
                receipt_file=receipt_file,
                notes=notes
            )
            
            # Return created payment
            response_serializer = InvestmentPaymentSerializer(payment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get investment statistics for a project."""
        project_id = pk
        
        # Get statistics
        stats = InvestmentService.get_project_investments_stats(project_id)
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get investment statistics for the current user."""
        user = request.user
        
        # Get user statistics
        stats = InvestmentService.get_user_investments_stats(user)
        
        return Response(stats)


class InvestmentPaymentViewSet(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.GenericViewSet):
    """
    API endpoint for investment payments.
    """
    queryset = InvestmentPayment.objects.all()
    serializer_class = InvestmentPaymentSerializer
    permission_classes = [IsAuthenticated, IsInvestorOrProjectCreator]
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update payment status.
        Project creators can mark payments as completed.
        """
        payment_id = pk
        new_status = request.data.get('status')
        
        # Update status
        payment = InvestmentService.update_payment_status(
            payment_id=payment_id,
            user=request.user,
            new_status=new_status
        )
        
        # Return updated payment
        serializer = self.get_serializer(payment)
        return Response(serializer.data) 