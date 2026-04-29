from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Merchant, Payout, LedgerEntry
from .serializers import MerchantSerializer, PayoutSerializer, LedgerEntrySerializer, PayoutRequestSerializer
from .services import get_available_balance, get_held_balance, request_payout, InsufficientFunds
from .tasks import process_payout

class MerchantBalanceView(APIView):
    def get(self, request, pk):
        merchant = get_object_or_404(Merchant, pk=pk)
        available = get_available_balance(merchant.id)
        held = get_held_balance(merchant.id)
        return Response({
            "available_balance_paise": available,
            "held_balance_paise": held,
            "currency": "INR"
        })

class MerchantTransactionsView(APIView):
    def get(self, request, pk):
        merchant = get_object_or_404(Merchant, pk=pk)
        entries = LedgerEntry.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        return Response(LedgerEntrySerializer(entries, many=True).data)

class MerchantPayoutsView(APIView):
    def get(self, request, pk):
        merchant = get_object_or_404(Merchant, pk=pk)
        payouts = Payout.objects.filter(merchant=merchant).order_by('-created_at')[:50]
        return Response(PayoutSerializer(payouts, many=True).data)

class PayoutRequestView(APIView):
    def post(self, request, pk):
        merchant = get_object_or_404(Merchant, pk=pk)
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount_paise = serializer.validated_data['amount_paise']
        bank_account_id = serializer.validated_data['bank_account_id']

        try:
            ik, created = request_payout(merchant.id, amount_paise, bank_account_id, idempotency_key)
            
            if not created:
                # Key already seen. If response exists, return it. Otherwise 409.
                if ik.response_status:
                    return Response(ik.response_body, status=ik.response_status)
                else:
                    return Response({"error": "Concurrent request in flight"}, status=status.HTTP_409_CONFLICT)
            
            # Key created, payout requested.
            resp_data = PayoutSerializer(ik.payout).data
            
            # Save response to IK
            ik.response_status = status.HTTP_201_CREATED
            ik.response_body = resp_data
            ik.save()

            # Trigger Celery Task asynchronously
            # Use transaction.on_commit to ensure task runs AFTER DB commits
            from django.db import transaction
            transaction.on_commit(lambda: process_payout.delay(ik.payout.id))

            return Response(resp_data, status=status.HTTP_201_CREATED)

        except InsufficientFunds:
            resp_data = {"error": "Insufficient funds"}
            # IK handling for failure
            # If it failed here, we already updated the IK in services.py (or we can do it here)
            return Response(resp_data, status=status.HTTP_400_BAD_REQUEST)

class PayoutDetailView(APIView):
    def get(self, request, pk):
        payout = get_object_or_404(Payout, pk=pk)
        return Response(PayoutSerializer(payout).data)
