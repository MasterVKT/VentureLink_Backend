"""
Views for repayment management.
"""
from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from apps.investments.models import Repayment, RepaymentSchedule
from apps.investments.serializers import (
    RepaymentSerializer, RepaymentListSerializer, RepaymentCreateSerializer,
    RepaymentUpdateSerializer, RepaymentStatusUpdateSerializer,
    RepaymentScheduleSerializer, RepaymentScheduleCreateSerializer
)
from apps.investments.services import RepaymentService, RepaymentScheduleService
from apps.core.permissions import IsAdminUser, IsInvestorOrProjectCreator


class RepaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for repayments.
    """
    permission_classes = [IsAuthenticated, IsInvestorOrProjectCreator]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'repayment_type']
    ordering_fields = ['created_at', 'due_date', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return repayments filtered by permissions."""
        user = self.request.user
        
        if user.is_staff:
            # Admin can see all repayments
            return Repayment.objects.all()
        
        # Filter by investment_id if provided
        investment_id = self.request.query_params.get('investment_id')
        status = self.request.query_params.get('status')
        repayment_type = self.request.query_params.get('repayment_type')
        
        return RepaymentService.get_repayments(
            user=user,
            investment_id=investment_id,
            status=status,
            repayment_type=repayment_type
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return RepaymentListSerializer
        elif self.action == 'create':
            return RepaymentCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return RepaymentUpdateSerializer
        elif self.action == 'update_status':
            return RepaymentStatusUpdateSerializer
        return RepaymentSerializer
    
    def perform_create(self, serializer):
        """Create repayment with current user as payer."""
        # Extract data from serializer
        investment_id = serializer.validated_data.get('investment_id')
        amount = serializer.validated_data.get('amount')
        currency = serializer.validated_data.get('currency')
        repayment_type = serializer.validated_data.get('repayment_type')
        principal_amount = serializer.validated_data.get('principal_amount')
        interest_amount = serializer.validated_data.get('interest_amount')
        payment_method = serializer.validated_data.get('payment_method')
        transaction_id = serializer.validated_data.get('transaction_id')
        payment_details = serializer.validated_data.get('payment_details')
        receipt_file = serializer.validated_data.get('receipt_file')
        notes = serializer.validated_data.get('notes')
        
        # Create repayment
        repayment = RepaymentService.create_repayment(
            user=self.request.user,
            investment_id=investment_id,
            amount=amount,
            currency=currency,
            repayment_type=repayment_type,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            payment_details=payment_details,
            receipt_file=receipt_file,
            notes=notes
        )
        
        # Save repayment to serializer
        serializer.instance = repayment
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update repayment status.
        Investors can mark repayments as completed after receiving them.
        """
        repayment_id = pk
        new_status = request.data.get('status')
        
        # Update status
        repayment = RepaymentService.update_repayment_status(
            repayment_id=repayment_id,
            user=request.user,
            new_status=new_status
        )
        
        # Return updated repayment
        serializer = self.get_serializer(repayment)
        return Response(serializer.data)


class RepaymentScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for repayment schedules.
    """
    queryset = RepaymentSchedule.objects.all()
    permission_classes = [IsAuthenticated, IsInvestorOrProjectCreator]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['investment', 'is_paid']
    ordering_fields = ['due_date', 'amount']
    ordering = ['due_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return RepaymentScheduleCreateSerializer
        return RepaymentScheduleSerializer
    
    @action(detail=False, methods=['post'])
    def create_schedule(self, request):
        """Create a repayment schedule for an investment."""
        investment_id = request.data.get('investment_id')
        items = request.data.get('items', [])
        
        if not investment_id:
            raise ValidationError({'investment_id': 'This field is required.'})
        
        if not items:
            raise ValidationError({'items': 'At least one schedule item is required.'})
        
        # Create schedule
        schedule_items = RepaymentScheduleService.create_schedule(
            investment_id=investment_id,
            user=request.user,
            schedule_items=items
        )
        
        # Return created items
        serializer = RepaymentScheduleSerializer(schedule_items, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def generate_loan_schedule(self, request):
        """Generate a loan repayment schedule for an investment."""
        investment_id = request.data.get('investment_id')
        start_date = request.data.get('start_date')
        payment_frequency_months = request.data.get('payment_frequency_months', 1)
        
        if not investment_id:
            raise ValidationError({'investment_id': 'This field is required.'})
        
        if not start_date:
            raise ValidationError({'start_date': 'This field is required.'})
        
        try:
            # Generate schedule
            schedule_items = RepaymentScheduleService.generate_loan_schedule(
                investment_id=investment_id,
                user=request.user,
                start_date=start_date,
                payment_frequency_months=payment_frequency_months
            )
            
            # Return created items
            serializer = RepaymentScheduleSerializer(schedule_items, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def link_repayment(self, request, pk=None):
        """Link a repayment to a schedule item."""
        schedule_item_id = pk
        repayment_id = request.data.get('repayment_id')
        
        if not repayment_id:
            raise ValidationError({'repayment_id': 'This field is required.'})
        
        try:
            # Link repayment
            schedule_item = RepaymentScheduleService.link_repayment_to_schedule(
                schedule_item_id=schedule_item_id,
                repayment_id=repayment_id,
                user=request.user
            )
            
            # Return updated item
            serializer = self.get_serializer(schedule_item)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST) 