"""
Service for repayment management.
"""
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from apps.investments.models import (
    Investment, Repayment, RepaymentSchedule
)


class RepaymentService:
    """Service class for repayments."""

    @staticmethod
    def get_repayments(user=None, investment_id=None, status=None, repayment_type=None):
        """
        Get repayments with optional filtering.
        
        Args:
            user: Optional user to filter repayments
            investment_id: Optional investment ID to filter repayments
            status: Optional status to filter repayments
            repayment_type: Optional repayment type to filter repayments
            
        Returns:
            QuerySet of Repayment objects
        """
        repayments = Repayment.objects.all()
        
        if user:
            # User can see repayments they paid or received
            repayments = repayments.filter(
                paid_by=user
            ) | repayments.filter(
                received_by=user
            )
            
        if investment_id:
            repayments = repayments.filter(investment_id=investment_id)
            
        if status:
            repayments = repayments.filter(status=status)
            
        if repayment_type:
            repayments = repayments.filter(repayment_type=repayment_type)
            
        return repayments.order_by('-created_at')

    @staticmethod
    def get_repayment_detail(repayment_id, user=None):
        """
        Get repayment detail.
        
        Args:
            repayment_id: The repayment ID
            user: Optional user to validate ownership
            
        Returns:
            Repayment object
            
        Raises:
            Repayment.DoesNotExist: If repayment not found
            PermissionDenied: If user is not authorized to view this repayment
        """
        repayment = Repayment.objects.get(id=repayment_id)
        
        # Check permissions if user is provided
        if user and not user.is_staff:
            # Allow access if user is payer or receiver
            if repayment.paid_by != user and repayment.received_by != user:
                raise PermissionDenied(_("Vous n'êtes pas autorisé à accéder à ce remboursement"))
        
        return repayment

    @staticmethod
    def create_repayment(user, investment_id, amount, currency, repayment_type,
                       principal_amount=None, interest_amount=None, payment_method=None,
                       transaction_id=None, payment_details=None, receipt_file=None, notes=None):
        """
        Create a new repayment.
        
        Args:
            user: User creating the repayment (project creator)
            investment_id: Target investment ID
            amount: Repayment amount
            currency: Currency code
            repayment_type: Type of repayment
            principal_amount: Optional principal amount
            interest_amount: Optional interest amount
            payment_method: Optional payment method
            transaction_id: Optional transaction ID
            payment_details: Optional payment details
            receipt_file: Optional receipt file
            notes: Optional notes
            
        Returns:
            Created Repayment object
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to create this repayment
        """
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.project.creator != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à créer un remboursement pour cet investissement"))
        
        # Create with transaction for consistency
        with transaction.atomic():
            # Create the repayment
            repayment = Repayment.objects.create(
                investment=investment,
                paid_by=user,
                received_by=investment.investor,
                amount=amount,
                currency=currency,
                repayment_type=repayment_type,
                principal_amount=principal_amount,
                interest_amount=interest_amount,
                payment_method=payment_method or Repayment.METHOD_BANK_TRANSFER,
                transaction_id=transaction_id,
                payment_details=payment_details,
                receipt_file=receipt_file,
                notes=notes,
                status=Repayment.STATUS_PENDING
            )
            
            return repayment

    @staticmethod
    def update_repayment_status(repayment_id, user, new_status):
        """
        Update repayment status.
        
        Args:
            repayment_id: The repayment ID
            user: User performing the status update
            new_status: New status to set
            
        Returns:
            Updated Repayment object
            
        Raises:
            Repayment.DoesNotExist: If repayment not found
            PermissionDenied: If user is not authorized to update this repayment
        """
        # Get repayment
        repayment = Repayment.objects.get(id=repayment_id)
        
        # Check permissions
        if repayment.received_by != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier le statut de ce remboursement"))
        
        # Update with transaction for consistency
        with transaction.atomic():
            # Handle status-specific actions
            if new_status == Repayment.STATUS_COMPLETED and repayment.status != Repayment.STATUS_COMPLETED:
                repayment.completed_at = timezone.now()
                
                # If this is linked to a schedule item, mark it as paid
                try:
                    schedule_item = RepaymentSchedule.objects.get(repayment=repayment)
                    schedule_item.is_paid = True
                    schedule_item.save(update_fields=['is_paid', 'updated_at'])
                except RepaymentSchedule.DoesNotExist:
                    pass
            
            # Update status
            repayment.status = new_status
            repayment.save()
            
            return repayment


class RepaymentScheduleService:
    """Service class for repayment schedules."""

    @staticmethod
    def get_schedule_items(investment_id=None, is_paid=None):
        """
        Get schedule items with optional filtering.
        
        Args:
            investment_id: Optional investment ID to filter items
            is_paid: Optional payment status to filter items
            
        Returns:
            QuerySet of RepaymentSchedule objects
        """
        items = RepaymentSchedule.objects.all()
        
        if investment_id:
            items = items.filter(investment_id=investment_id)
            
        if is_paid is not None:
            items = items.filter(is_paid=is_paid)
            
        return items.order_by('due_date')

    @staticmethod
    def get_schedule_item_detail(item_id, user=None):
        """
        Get schedule item detail.
        
        Args:
            item_id: The schedule item ID
            user: Optional user to validate ownership
            
        Returns:
            RepaymentSchedule object
            
        Raises:
            RepaymentSchedule.DoesNotExist: If item not found
            PermissionDenied: If user is not authorized to view this item
        """
        item = RepaymentSchedule.objects.get(id=item_id)
        
        # Check permissions if user is provided
        if user and not user.is_staff:
            # Allow access if user is investor or project creator
            investment = item.investment
            if investment.investor != user and investment.project.creator != user:
                raise PermissionDenied(_("Vous n'êtes pas autorisé à accéder à cette échéance"))
        
        return item

    @staticmethod
    def create_schedule(investment_id, user, schedule_items):
        """
        Create a repayment schedule for an investment.
        
        Args:
            investment_id: The investment ID
            user: User creating the schedule (project creator)
            schedule_items: List of schedule items (due_date, amount, principal_amount, interest_amount, etc.)
            
        Returns:
            List of created RepaymentSchedule objects
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to create this schedule
        """
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.project.creator != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à créer un échéancier pour cet investissement"))
        
        # Create with transaction for consistency
        created_items = []
        with transaction.atomic():
            for item_data in schedule_items:
                item = RepaymentSchedule.objects.create(
                    investment=investment,
                    due_date=item_data['due_date'],
                    amount=item_data['amount'],
                    principal_amount=item_data['principal_amount'],
                    interest_amount=item_data['interest_amount'],
                    currency=item_data.get('currency', investment.currency),
                    notes=item_data.get('notes')
                )
                created_items.append(item)
            
        return created_items

    @staticmethod
    def generate_loan_schedule(investment_id, user, start_date, payment_frequency_months=1):
        """
        Generate a loan repayment schedule for an investment.
        
        Args:
            investment_id: The investment ID
            user: User generating the schedule (project creator)
            start_date: Date of first payment
            payment_frequency_months: Months between payments
            
        Returns:
            List of created RepaymentSchedule objects
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to create this schedule
            ValueError: If investment is not a loan
        """
        from dateutil.relativedelta import relativedelta
        
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.project.creator != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à créer un échéancier pour cet investissement"))
        
        # Verify investment is a loan
        if investment.investment_type != Investment.TYPE_LOAN:
            raise ValueError(_("L'échéancier automatique est disponible uniquement pour les investissements de type prêt"))
        
        # Verify required parameters
        if not investment.term_months or not investment.interest_rate:
            raise ValueError(_("Le prêt doit avoir une durée et un taux d'intérêt définis"))
        
        # Calculate total number of payments
        num_payments = investment.term_months // payment_frequency_months
        if investment.term_months % payment_frequency_months > 0:
            num_payments += 1
        
        # Simple interest calculation
        principal_per_payment = investment.amount / num_payments
        total_interest = investment.amount * (investment.interest_rate / 100) * (investment.term_months / 12)
        interest_per_payment = total_interest / num_payments
        
        # Generate schedule
        schedule_items = []
        for i in range(num_payments):
            due_date = start_date + relativedelta(months=i * payment_frequency_months)
            
            item_data = {
                'due_date': due_date,
                'amount': principal_per_payment + interest_per_payment,
                'principal_amount': principal_per_payment,
                'interest_amount': interest_per_payment,
                'currency': investment.currency,
                'notes': f"Paiement {i+1}/{num_payments}"
            }
            schedule_items.append(item_data)
        
        # Create schedule
        return RepaymentScheduleService.create_schedule(investment_id, user, schedule_items)

    @staticmethod
    def link_repayment_to_schedule(schedule_item_id, repayment_id, user):
        """
        Link a repayment to a schedule item.
        
        Args:
            schedule_item_id: The schedule item ID
            repayment_id: The repayment ID
            user: User performing the linking
            
        Returns:
            Updated RepaymentSchedule object
            
        Raises:
            RepaymentSchedule.DoesNotExist: If item not found
            Repayment.DoesNotExist: If repayment not found
            PermissionDenied: If user is not authorized
        """
        # Get items
        schedule_item = RepaymentSchedule.objects.get(id=schedule_item_id)
        repayment = Repayment.objects.get(id=repayment_id)
        
        # Check permissions
        if schedule_item.investment.project.creator != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à lier ce remboursement"))
        
        # Verify they belong to the same investment
        if schedule_item.investment.id != repayment.investment.id:
            raise ValueError(_("L'échéance et le remboursement doivent appartenir au même investissement"))
        
        # Update with transaction for consistency
        with transaction.atomic():
            # Link them
            schedule_item.repayment = repayment
            
            # If repayment is completed, mark schedule item as paid
            if repayment.status == Repayment.STATUS_COMPLETED:
                schedule_item.is_paid = True
            
            schedule_item.save()
            
            return schedule_item 