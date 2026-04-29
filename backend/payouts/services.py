from django.db import transaction, IntegrityError
from django.db.models import Sum, F, Case, When, BigIntegerField
from django.utils import timezone
from .models import Merchant, LedgerEntry, Payout, IdempotencyKey
from .state_machine import transition_payout
import uuid

class InsufficientFunds(Exception):
    pass

def get_available_balance(merchant_id):
    """
    Computes the available balance for a merchant directly in the DB.
    Balance = sum of credits - sum of debits.
    """
    result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        balance=Sum(
            Case(
                When(entry_type='CREDIT', then=F('amount_paise')),
                default=-F('amount_paise'),
                output_field=BigIntegerField()
            )
        )
    )
    return result['balance'] or 0

def get_held_balance(merchant_id):
    """
    Held balance is the sum of payouts that are either PENDING or PROCESSING.
    """
    result = Payout.objects.filter(
        merchant_id=merchant_id, 
        status__in=['PENDING', 'PROCESSING']
    ).aggregate(
        held=Sum('amount_paise')
    )
    return result['held'] or 0

def _get_balance_internal(merchant_id):
    # Same as above but expects to be used where Case, When, models are imported
    from django.db import models
    from django.db.models import Case, When, Sum, F
    result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        balance=Sum(
            Case(
                When(entry_type='CREDIT', then=F('amount_paise')),
                default=-F('amount_paise'),
                output_field=models.BigIntegerField()
            )
        )
    )
    return result['balance'] or 0

@transaction.atomic
def request_payout(merchant_id, amount_paise, bank_account_id, idempotency_key_str):
    """
    Handles a payout request with concurrency control and idempotency.
    """
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    
    # 1. Idempotency Check
    ik, created = IdempotencyKey.objects.get_or_create(
        merchant=merchant,
        key=idempotency_key_str,
        defaults={'expires_at': timezone.now() + timezone.timedelta(hours=24)}
    )
    if not created:
        if ik.is_expired():
            pass
        return ik, False # False means not created

    # 2. Balance Check
    available = _get_balance_internal(merchant.id)
    if available < amount_paise:
        # Before raising, we should probably mark IK as failed with 400.
        ik.response_status = 400
        ik.response_body = {"error": "Insufficient funds"}
        ik.save()
        raise InsufficientFunds("Balance too low")

    # 3. Create Payout
    payout = Payout.objects.create(
        merchant=merchant,
        amount_paise=amount_paise,
        bank_account_id=bank_account_id,
        status='PENDING',
        idempotency_key=ik
    )

    # 4. Debit Ledger
    LedgerEntry.objects.create(
        merchant=merchant,
        entry_type='DEBIT',
        amount_paise=amount_paise,
        reference=str(payout.id),
        description=f"Withdrawal to {bank_account_id}"
    )

    # Update IK
    ik.payout = payout
    ik.save()

    return ik, True # True means newly created
