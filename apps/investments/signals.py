"""
Signal receivers for the investments app.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.investments.models import Investment, InvestmentHistory, InvestmentPayment, Repayment


@receiver(post_save, sender=Investment)
def create_initial_investment_history(sender, instance, created, **kwargs):
    """
    Create initial investment history when a new investment is created.
    """
    if created:
        InvestmentHistory.objects.create(
            investment=instance,
            user=instance.investor,
            new_status=instance.status,
            comment="Investissement créé"
        )


@receiver(pre_save, sender=Investment)
def update_investment_timestamps(sender, instance, **kwargs):
    """
    Update timestamps based on investment status.
    """
    if instance.pk:
        # Get the previous state
        previous = Investment.objects.get(pk=instance.pk)
        
        # If status changed to APPROVED, set approved_at
        if instance.status == Investment.STATUS_APPROVED and previous.status != Investment.STATUS_APPROVED:
            instance.approved_at = timezone.now()
            
        # If status changed to COMPLETED, set completed_at
        if instance.status == Investment.STATUS_COMPLETED and previous.status != Investment.STATUS_COMPLETED:
            instance.completed_at = timezone.now()


@receiver(post_save, sender=InvestmentPayment)
def update_investment_on_payment(sender, instance, created, **kwargs):
    """
    Update investment status if all payments are completed.
    """
    from django.db.models import Sum
    
    # Only process if payment status is COMPLETED
    if instance.status == InvestmentPayment.STATUS_COMPLETED:
        investment = instance.investment
        
        # If investment is approved, check if all payments are completed
        if investment.status == Investment.STATUS_APPROVED:
            # Calculate total paid amount
            total_paid = InvestmentPayment.objects.filter(
                investment=investment,
                status=InvestmentPayment.STATUS_COMPLETED,
                currency=investment.currency
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Check if total paid amount equals or exceeds investment amount
            if total_paid >= investment.amount:
                # Update investment status to COMPLETED
                investment.status = Investment.STATUS_COMPLETED
                investment.completed_at = timezone.now()
                investment.save()
                
                # Create history entry
                InvestmentHistory.objects.create(
                    investment=investment,
                    user=None,  # System update
                    old_status=Investment.STATUS_APPROVED,
                    new_status=Investment.STATUS_COMPLETED,
                    comment="Investissement complété suite au paiement total"
                )


@receiver(post_save, sender=Repayment)
def update_repayment_schedule_on_completion(sender, instance, **kwargs):
    """
    Update repayment schedule when a repayment is completed.
    """
    # Only process if repayment status is COMPLETED
    if instance.status == Repayment.STATUS_COMPLETED:
        # Check if this repayment is linked to a schedule item
        try:
            schedule_item = instance.schedule_item
            if schedule_item:
                schedule_item.is_paid = True
                schedule_item.save(update_fields=['is_paid'])
        except Repayment._meta.get_field('schedule_item').related_model.DoesNotExist:
            pass 