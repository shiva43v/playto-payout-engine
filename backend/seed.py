import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from payouts.models import Merchant, LedgerEntry

def run():
    print("Seeding database...")
    
    Merchant.objects.all().delete()
    
    # Create a few merchants
    m1 = Merchant.objects.create(name="Acme Agency", email="hello@acme.com")
    m2 = Merchant.objects.create(name="Freelance Bob", email="bob@freelance.com")
    m3 = Merchant.objects.create(name="Dev Studio", email="hi@devstudio.com")

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
