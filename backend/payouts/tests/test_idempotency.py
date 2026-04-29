from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import uuid
from payouts.models import Merchant, LedgerEntry, Payout

class IdempotencyTestCase(APITestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Merchant", email="test@test.com")
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type='CREDIT',
            amount_paise=10000,
            reference="TEST-INIT",
            description="Initial"
        )
        self.url = reverse('payout-request', kwargs={'pk': self.merchant.id})

    def test_idempotent_requests(self):
        idempotency_key = str(uuid.uuid4())
        data = {
            "amount_paise": 1000,
            "bank_account_id": "BANK123"
        }
        headers = {
            "HTTP_IDEMPOTENCY_KEY": idempotency_key
        }

        # First request
        response1 = self.client.post(self.url, data, format='json', **headers)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payout.objects.count(), 1)
        payout1_id = response1.data['id']

        # Second request with same key
        response2 = self.client.post(self.url, data, format='json', **headers)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payout.objects.count(), 1) # Still 1 payout
        self.assertEqual(response2.data['id'], payout1_id) # Same payout returned
        
        # Second request with different key
        headers2 = {
            "HTTP_IDEMPOTENCY_KEY": str(uuid.uuid4())
        }
        response3 = self.client.post(self.url, data, format='json', **headers2)
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payout.objects.count(), 2) # Now 2 payouts
