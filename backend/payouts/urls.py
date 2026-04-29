from django.urls import path
from .views import MerchantBalanceView, MerchantTransactionsView, MerchantPayoutsView, PayoutRequestView, PayoutDetailView

urlpatterns = [
    path('merchants/<uuid:pk>/balance', MerchantBalanceView.as_view(), name='merchant-balance'),
    path('merchants/<uuid:pk>/transactions', MerchantTransactionsView.as_view(), name='merchant-transactions'),
    path('merchants/<uuid:pk>/payouts', MerchantPayoutsView.as_view(), name='merchant-payouts-list'),
    path('merchants/<uuid:pk>/request-payout', PayoutRequestView.as_view(), name='payout-request'),
    path('payouts/<uuid:pk>', PayoutDetailView.as_view(), name='payout-detail'),
]
