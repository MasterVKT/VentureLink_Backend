"""
Service for investment management.
"""
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from apps.investments.models import (
    Investment, InvestmentHistory, InvestmentPayment
)
from apps.projects.models import Project
from apps.users.models import User


class InvestmentService:
    """Service class for investments."""

    @staticmethod
    def get_investments(user=None, project_id=None, status=None, investment_type=None):
        """
        Get investments with optional filtering.
        
        Args:
            user: Optional user to filter investments by investor
            project_id: Optional project ID to filter investments
            status: Optional status to filter investments
            investment_type: Optional investment type to filter investments
            
        Returns:
            QuerySet of Investment objects
        """
        investments = Investment.objects.all()
        
        if user:
            investments = investments.filter(investor=user)
            
        if project_id:
            investments = investments.filter(project_id=project_id)
            
        if status:
            investments = investments.filter(status=status)
            
        if investment_type:
            investments = investments.filter(investment_type=investment_type)
            
        return investments.order_by('-created_at')

    @staticmethod
    def get_investment_detail(investment_id, user=None):
        """
        Get investment detail.
        
        Args:
            investment_id: The investment ID
            user: Optional user to validate ownership
            
        Returns:
            Investment object
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to view this investment
        """
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions if user is provided
        if user and not user.is_staff:
            # Allow access if user is investor or project creator
            if investment.investor != user and investment.project.creator != user:
                raise PermissionDenied(_("Vous n'êtes pas autorisé à accéder à cet investissement"))
        
        return investment

    @staticmethod
    def create_investment(user, project_id, amount, currency, investment_type,
                         equity_percentage=None, interest_rate=None, term_months=None,
                         description=None):
        """
        Create a new investment.
        
        Args:
            user: User creating the investment (investor)
            project_id: Target project ID
            amount: Investment amount
            currency: Currency code
            investment_type: Type of investment
            equity_percentage: Optional equity percentage for equity investments
            interest_rate: Optional interest rate for loan investments
            term_months: Optional term in months for loan investments
            description: Optional description
            
        Returns:
            Created Investment object
            
        Raises:
            Project.DoesNotExist: If project not found
            ValidationError: If investment data is invalid
        """
        # Get project
        project = Project.objects.get(id=project_id)
        
        # Validate the project is active
        if project.status != Project.STATUS_ACTIVE or project.is_draft:
            raise PermissionDenied(_("Ce projet n'accepte pas les investissements actuellement"))
        
        # Create investment with transaction for consistency
        with transaction.atomic():
            # Create the investment
            investment = Investment.objects.create(
                investor=user,
                project=project,
                amount=amount,
                currency=currency,
                investment_type=investment_type,
                equity_percentage=equity_percentage,
                interest_rate=interest_rate,
                term_months=term_months,
                description=description,
                status=Investment.STATUS_PENDING
            )
            
            # Create initial history entry
            InvestmentHistory.objects.create(
                investment=investment,
                user=user,
                old_status=None,
                new_status=Investment.STATUS_PENDING,
                comment=_("Investissement créé")
            )
            
            return investment

    @staticmethod
    def update_investment(investment_id, user, data):
        """
        Update an investment.
        
        Args:
            investment_id: The investment ID
            user: User performing the update
            data: Dictionary with fields to update
            
        Returns:
            Updated Investment object
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to update this investment
        """
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.investor != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier cet investissement"))
        
        # Check if investment is in a state that allows updates
        if investment.status not in [Investment.STATUS_PENDING]:
            raise PermissionDenied(_("Cet investissement ne peut plus être modifié"))
        
        # Update fields
        for field, value in data.items():
            if hasattr(investment, field) and field not in ['investor', 'project', 'status']:
                setattr(investment, field, value)
        
        investment.save()
        return investment

    @staticmethod
    def update_investment_status(investment_id, user, new_status, comment=None):
        """
        Update investment status.
        
        Args:
            investment_id: The investment ID
            user: User performing the status update
            new_status: New status to set
            comment: Optional comment explaining the status change
            
        Returns:
            Updated Investment object
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to update this investment
        """
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.project.creator != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier le statut de cet investissement"))
        
        # Get old status for history
        old_status = investment.status
        
        # Update with transaction for consistency
        with transaction.atomic():
            # Handle status-specific actions
            if new_status == Investment.STATUS_APPROVED and old_status != Investment.STATUS_APPROVED:
                investment.approved_at = timezone.now()
            
            if new_status == Investment.STATUS_COMPLETED and old_status != Investment.STATUS_COMPLETED:
                investment.completed_at = timezone.now()
            
            # Update status
            investment.status = new_status
            investment.save()
            
            # Create history entry
            InvestmentHistory.objects.create(
                investment=investment,
                user=user,
                old_status=old_status,
                new_status=new_status,
                comment=comment
            )
            
            return investment

    @staticmethod
    def create_payment(investment_id, user, amount, currency, payment_method,
                      transaction_id=None, payment_details=None, receipt_file=None, notes=None):
        """
        Create a payment for an investment.
        
        Args:
            investment_id: The investment ID
            user: User creating the payment
            amount: Payment amount
            currency: Currency code
            payment_method: Method of payment
            transaction_id: Optional transaction ID
            payment_details: Optional payment details
            receipt_file: Optional receipt file
            notes: Optional notes
            
        Returns:
            Created InvestmentPayment object
            
        Raises:
            Investment.DoesNotExist: If investment not found
            PermissionDenied: If user is not authorized to create a payment
        """
        # Get investment
        investment = Investment.objects.get(id=investment_id)
        
        # Check permissions
        if investment.investor != user and not user.is_staff:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à ajouter un paiement à cet investissement"))
        
        # Create payment with transaction for consistency
        with transaction.atomic():
            payment = InvestmentPayment.objects.create(
                investment=investment,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                transaction_id=transaction_id,
                payment_details=payment_details,
                receipt_file=receipt_file,
                notes=notes,
                status=InvestmentPayment.STATUS_PENDING
            )
            
            return payment

    @staticmethod
    def update_payment_status(payment_id, user, new_status):
        """
        Update payment status.
        
        Args:
            payment_id: The payment ID
            user: User updating the status
            new_status: New status to set
            
        Returns:
            Updated InvestmentPayment object
            
        Raises:
            InvestmentPayment.DoesNotExist: If payment not found
            PermissionDenied: If user is not authorized to update payment status
        """
        # Get payment
        payment = InvestmentPayment.objects.get(id=payment_id)
        
        # Check permissions
        if not user.is_staff and payment.investment.project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier le statut de ce paiement"))
        
        # Update with transaction for consistency
        with transaction.atomic():
            # Handle status-specific actions
            if new_status == InvestmentPayment.STATUS_COMPLETED and payment.status != InvestmentPayment.STATUS_COMPLETED:
                payment.completed_at = timezone.now()
                
                # If payment is now completed, also update investment status if appropriate
                if payment.amount >= payment.investment.amount and payment.investment.status == Investment.STATUS_APPROVED:
                    InvestmentService.update_investment_status(
                        payment.investment.id,
                        user,
                        Investment.STATUS_COMPLETED,
                        _("Paiement complet reçu et vérifié")
                    )
            
            # Update status
            payment.status = new_status
            payment.save()
            
            return payment

    @staticmethod
    def get_project_investments_stats(project_id):
        """
        Get investment statistics for a project.
        
        Args:
            project_id: The project ID
            
        Returns:
            Dict with investment statistics
        """
        # Get all completed investments for the project
        completed_investments = Investment.objects.filter(
            project_id=project_id,
            status=Investment.STATUS_COMPLETED
        )
        
        # Calculate total invested amount by type, handling null values
        total_equity = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_EQUITY)
            if inv.amount is not None
        ) or 0
        
        total_loan = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_LOAN)
            if inv.amount is not None
        ) or 0
        
        total_donation = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_DONATION)
            if inv.amount is not None
        ) or 0
        
        total_convertible = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_CONVERTIBLE_NOTE)
            if inv.amount is not None
        ) or 0
        
        # Get total invested amount
        total_invested = total_equity + total_loan + total_donation + total_convertible
        
        # Return statistics with guaranteed numeric values
        return {
            'total_invested': float(total_invested) if total_invested else 0.0,
            'total_equity': float(total_equity) if total_equity else 0.0,
            'total_loan': float(total_loan) if total_loan else 0.0,
            'total_donation': float(total_donation) if total_donation else 0.0,
            'total_convertible_note': float(total_convertible) if total_convertible else 0.0,
            'investors_count': completed_investments.values('investor').distinct().count(),
            'investments_count': completed_investments.count()
        }

    @staticmethod
    def get_user_investments_stats(user):
        """
        Get investment statistics for a user.
        
        Args:
            user: The user to get statistics for
            
        Returns:
            Dict with user investment statistics
        """
        # Get all user investments
        user_investments = Investment.objects.filter(investor=user)
        
        # Filter by status
        pending_investments = user_investments.filter(status=Investment.STATUS_PENDING)
        approved_investments = user_investments.filter(status=Investment.STATUS_APPROVED)
        completed_investments = user_investments.filter(status=Investment.STATUS_COMPLETED)
        rejected_investments = user_investments.filter(status=Investment.STATUS_REJECTED)
        
        # Calculate total invested amount by type, handling null values
        total_equity = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_EQUITY)
            if inv.amount is not None
        ) or 0
        
        total_loan = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_LOAN)
            if inv.amount is not None
        ) or 0
        
        total_donation = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_DONATION)
            if inv.amount is not None
        ) or 0
        
        total_convertible = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_CONVERTIBLE_NOTE)
            if inv.amount is not None
        ) or 0
        
        # Get total invested amount
        total_invested = total_equity + total_loan + total_donation + total_convertible
        
        # Return statistics with guaranteed numeric values
        return {
            'total_invested': float(total_invested) if total_invested else 0.0,
            'total_equity': float(total_equity) if total_equity else 0.0,
            'total_loan': float(total_loan) if total_loan else 0.0,
            'total_donation': float(total_donation) if total_donation else 0.0,
            'total_convertible_note': float(total_convertible) if total_convertible else 0.0,
            'investments_count': user_investments.count(),
            'pending_count': pending_investments.count(),
            'approved_count': approved_investments.count(),
            'completed_count': completed_investments.count(),
            'rejected_count': rejected_investments.count(),
            'projects_count': user_investments.values('project').distinct().count()
        }

    @staticmethod
    def get_public_investment_stats():
        """
        Get public investment statistics accessible to anonymous users.
        
        Returns:
            Dict with public investment statistics
        """
        # Get all completed investments for public statistics
        completed_investments = Investment.objects.filter(
            status=Investment.STATUS_COMPLETED
        )
        
        # Calculate total invested amount by type, handling null values
        total_equity = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_EQUITY)
            if inv.amount is not None
        ) or 0
        
        total_loan = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_LOAN)
            if inv.amount is not None
        ) or 0
        
        total_donation = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_DONATION)
            if inv.amount is not None
        ) or 0
        
        total_convertible = sum(
            inv.amount for inv in completed_investments.filter(investment_type=Investment.TYPE_CONVERTIBLE_NOTE)
            if inv.amount is not None
        ) or 0
        
        # Get total invested amount
        total_invested = total_equity + total_loan + total_donation + total_convertible
        
        # Get total number of funded projects
        funded_projects_count = completed_investments.values('project').distinct().count()
        
        # Get total number of investors
        total_investors_count = completed_investments.values('investor').distinct().count()
        
        # Return public statistics with guaranteed numeric values
        return {
            'total_invested': float(total_invested) if total_invested else 0.0,
            'total_equity': float(total_equity) if total_equity else 0.0,
            'total_loan': float(total_loan) if total_loan else 0.0,
            'total_donation': float(total_donation) if total_donation else 0.0,
            'total_convertible_note': float(total_convertible) if total_convertible else 0.0,
            'funded_projects_count': funded_projects_count,
            'total_investors_count': total_investors_count,
            'total_investments_count': completed_investments.count()
        } 