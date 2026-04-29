# EXPLAINER.md

## 1. The Ledger

**Calculation Query:**
```python
def get_available_balance(merchant_id):
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
```

**Why model credits and debits this way?**
By making the balance derived via an aggregate SQL query on append-only ledger entries, we completely eliminate drift. The balance is mathematically guaranteed to equal `SUM(credits) - SUM(debits)`. The alternative (keeping a `balance` column on the `Merchant` model) requires double-entry accounting updates and is prone to desyncs if an update fails or is bypassed.

## 2. The Lock

**Exact code:**
```python
@transaction.atomic
def request_payout(merchant_id, amount_paise, bank_account_id, idempotency_key_str):
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    # ... balance checks and ledger debit ...
```

**What database primitive it relies on:**
It relies on PostgreSQL's `SELECT ... FOR UPDATE` which applies a **row-level exclusive lock** to the merchant's row. When two requests arrive simultaneously, the first acquires the lock. The second request blocks until the first transaction commits or rolls back. Once unblocked, the second request reads the freshly updated balance computed via the ledger aggregate and correctly rejects if funds are now insufficient. 

## 3. The Idempotency

**How it knows it has seen a key before:**
We have a unique database constraint (`unique_together = ('merchant', 'key')`) on the `IdempotencyKey` model. When a request arrives, we try `get_or_create`. If `created` is False, we know it's a duplicate.

**What happens if the first request is in flight when the second arrives?**
The first request creates the `IdempotencyKey` row but hasn't yet saved a `response_status` or `response_body` to it. If the second request arrives, it pulls the existing key. We check if it has a saved response. If not, it means the first request is still processing, so the second request instantly returns a `409 Conflict` (or similar) preventing duplicate execution while the first finishes.

## 4. The State Machine

**Where is failed-to-completed blocked?**
In `backend/payouts/state_machine.py`:
```python
VALID_TRANSITIONS = {
    'PENDING': ['PROCESSING'],
    'PROCESSING': ['COMPLETED', 'FAILED'],
    'COMPLETED': [],
    'FAILED': []
}

def transition_payout(payout, new_status):
    if new_status not in VALID_TRANSITIONS.get(payout.status, []):
        raise InvalidTransition(f"Illegal transition: {payout.status} -> {new_status}")
    # ...
```
Because `'FAILED'` has an empty list of valid next states, attempting `transition_payout(payout, 'COMPLETED')` on a failed payout will throw an `InvalidTransition` exception.

## 5. The AI Audit

**What AI wrote subtly wrong initially:**
1. AI initially suggested using `try/except IntegrityError` with `IdempotencyKey.objects.create()` inside the `@transaction.atomic` block in `request_payout`.
2. AI didn't import `Case` and `When` correctly.
3. AI tried to serialize a UUID directly into a `JSONField` without a proper encoder.

**What I caught & replaced:**
Catching `IntegrityError` from a unique constraint violation *breaks* the surrounding Django database transaction (PostgreSQL aborts the transaction). You can't run any more queries (like `get()` or returning data) in that block, leading to `TransactionManagementError`. I replaced it with `IdempotencyKey.objects.get_or_create()`, which uses an internal savepoint (sub-transaction) explicitly to handle the race condition safely without aborting the outer `atomic` block. 
I also added `DjangoJSONEncoder` to the `JSONField` to handle UUID serialization properly.
