import time
import random
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import Payout, LedgerEntry
from .state_machine import transition_payout, InvalidTransition

@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id):
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return
    
    if payout.status != 'PENDING' and payout.status != 'PROCESSING':
        return # Already done or failed
        
    try:
        transition_payout(payout, 'PROCESSING')
    except InvalidTransition:
        return

    # Simulate bank settlement network
    # 80% success, 20% fail
    outcome = random.choices(['success', 'fail'], weights=[80, 20])[0]

    payout.attempts += 1
    payout.last_attempt_at = timezone.now()
    payout.save(update_fields=['attempts', 'last_attempt_at'])

    time.sleep(1) # Simulate network delay

    try:
        if outcome == 'success':
            with transaction.atomic():
                # Refresh from db and lock it
                payout = Payout.objects.select_for_update().get(id=payout.id)
                if payout.status != 'PROCESSING':
                    return "Already processed"
                transition_payout(payout, 'COMPLETED')
            return "Completed"

        elif outcome == 'fail':
            # Return funds atomically with state transition
            with transaction.atomic():
                payout = Payout.objects.select_for_update().get(id=payout.id)
                if payout.status != 'PROCESSING':
                    return "Already processed"
                
                payout.failure_reason = "Simulated bank rejection"
                transition_payout(payout, 'FAILED')
                payout.save(update_fields=['failure_reason'])

                # Credit back the merchant
                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    entry_type='CREDIT',
                    amount_paise=payout.amount_paise,
                    reference=str(payout.id),
                    description="Refund for failed payout"
                )
            return "Failed and refunded"
    except Exception as e:
        # If any unexpected error occurs (e.g., DB connection drop on free tier),
        # ensure we don't leave the payout stuck in PROCESSING.
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout.id)
            if payout.status == 'PROCESSING':
                payout.failure_reason = f"Internal system error: {str(e)}"
                transition_payout(payout, 'FAILED')
                payout.save(update_fields=['failure_reason'])
                # Credit back the merchant
                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    entry_type='CREDIT',
                    amount_paise=payout.amount_paise,
                    reference=str(payout.id),
                    description="Refund due to internal error"
                )
        return "Failed due to exception"


@shared_task
def retry_stuck_payouts():
    """
    Periodic task that runs every 30s.
    Finds payouts in PROCESSING state where updated_at < now - 30s.
    """
    cutoff_time = timezone.now() - timezone.timedelta(seconds=30)
    
    stuck_payouts = Payout.objects.filter(
        status='PROCESSING',
        updated_at__lt=cutoff_time
    )

    for payout in stuck_payouts:
        # Check attempts
        if payout.attempts >= 3:
            # Mark as failed permanently
            with transaction.atomic():
                payout = Payout.objects.select_for_update().get(id=payout.id)
                if payout.status != 'PROCESSING':
                    continue
                payout.failure_reason = "Max retries exceeded"
                transition_payout(payout, 'FAILED')
                payout.save(update_fields=['failure_reason'])

                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    entry_type='CREDIT',
                    amount_paise=payout.amount_paise,
                    reference=str(payout.id),
                    description="Refund for stuck/failed payout"
                )
        else:
            # Exponential backoff check
            # min(30 * 2^attempt, 300)
            backoff_seconds = min(30 * (2 ** payout.attempts), 300)
            if payout.last_attempt_at and (timezone.now() - payout.last_attempt_at).total_seconds() < backoff_seconds:
                continue # Skip, not time yet
            
            # Re-enqueue
            process_payout.delay(payout.id)
