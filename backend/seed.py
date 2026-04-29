import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from payouts.models import Merchant, LedgerEntry

def run():
    print("Seeding database...")
    
    Merchant.objects.all().delete()
    
    # Create a few merchants with fixed IDs so you know exactly how to login
    m1_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
    m2_id = uuid.UUID('22222222-2222-2222-2222-222222222222')
    m3_id = uuid.UUID('33333333-3333-3333-3333-333333333333')

    m1 = Merchant.objects.create(id=m1_id, name="Acme Agency", email="hello@acme.com")
    m2 = Merchant.objects.create(id=m2_id, name="Freelance Bob", email="bob@freelance.com")
    m3 = Merchant.objects.create(id=m3_id, name="Dev Studio", email="hi@devstudio.com")

    # Give them some initial balances via CREDIT
    # M1: 50,000.00 USD -> let's say they have 100,000.00 INR = 10,000,000 paise
    LedgerEntry.objects.create(
        merchant=m1,
        entry_type='CREDIT',
        amount_paise=10000000,
        reference="PAY-INIT-1",
        description="Initial customer payment"
    )

    # M2: 50,000.00 INR = 5,000,000 paise
    LedgerEntry.objects.create(
        merchant=m2,
        entry_type='CREDIT',
        amount_paise=5000000,
        reference="PAY-INIT-2",
        description="Initial customer payment"
    )

    # M3: 10,000.00 INR = 1,000,000 paise
    LedgerEntry.objects.create(
        merchant=m3,
        entry_type='CREDIT',
        amount_paise=1000000,
        reference="PAY-INIT-3",
        description="Initial customer payment"
    )

    print("Seed complete!")
    print(f"Merchant 1: {m1.id} (Acme Agency)")
    print(f"Merchant 2: {m2.id} (Freelance Bob)")
    print(f"Merchant 3: {m3.id} (Dev Studio)")

if __name__ == '__main__':
    run()
