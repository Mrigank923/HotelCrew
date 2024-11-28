from .views import *
from django.urls import path

urlpatterns = [
    path('wallet/', walletView.as_view(), name='wallet'),
    path('transaction/', MakeTransactionView.as_view(), name='transaction'),
    path('transactions/', TransactionView.as_view(), name='transactions'),
]