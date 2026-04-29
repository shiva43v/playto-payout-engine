import threading
import uuid
from django.test import TransactionTestCase
from django.db import connection
from payouts.models import Merchant, LedgerEntry
from payouts.services import request_payout, InsufficientFunds, get_available_balance

class ConcurrencyTestCase(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Merchant", email="test@test.com")
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type='CREDIT',
            amount_paise=10000, # 100 rupees
            reference="TEST-INIT",
            description="Initial"
        )

    def test_concurrent_payouts_prevent_overdraw(self):
        # We need to simulate two concurrent requests that together exceed the balance,
        # but individually are within the balance. (e.g. 6000 and 6000).
        
        exceptions = []
        successes = []

        def make_request():
            try:
                # Need to close connection for the thread to get its own
                connection.close()
                ik, created = request_payout(
                    merchant_id=self.merchant.id,
                    amount_paise=6000,
                    bank_account_id="BANK123",
                    idempotency_key_str=str(uuid.uuid4())
                )
                successes.append(ik)
            except Exception as e:
                exceptions.append(e)
            finally:
                connection.close()

        t1 = threading.Thread(target=make_request)
        t2 = threading.Thread(target=make_request)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # One should succeed, one should fail due to InsufficientFunds
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(exceptions), 1)
        self.assertIsInstance(exceptions[0], InsufficientFunds)

        # The balance should be exactly 4000 (10000 - 6000)
        self.assertEqual(get_available_balance(self.merchant.id), 4000)
