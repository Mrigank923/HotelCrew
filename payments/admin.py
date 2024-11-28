from django.contrib import admin
from .models import *

@admin.register(wallet)
class walletAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'balance')
    search_fields = ('user__email', 'user__user_name')
    list_filter = ('user',)

@admin.register(Transaction)
class Transaction(admin.ModelAdmin):
    list_display = ('id','wallet', 'amount', 'transaction_type')
    search_fields = ('wallet__user__email', 'wallet__user__user_name')
    list_filter = ('wallet', 'transaction_type')
