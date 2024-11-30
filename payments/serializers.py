from .models import wallet, Transaction
from rest_framework import serializers
from hoteldetails.utils import get_hotel
import random
from authentication.models import User
import uuid

class walletserializer(serializers.ModelSerializer):
    class Meta:
        model = wallet
        fields = ['id','user', 'hotel', 'balance', 'created_at', 'wallet_id']
        read_only_fields = ['id','user', 'hotel', 'created_at', 'wallet_id']
    def create(self, validated_data):
        user = self.context['request'].user        
        hotel = get_hotel(user)
        if not hotel:
            raise serializers.ValidationError("Hotel information is required for wallet creation.")

        wallet_id = random.randint(100000000000, 999999999999)

        wallet_obj = wallet.objects.create(user=user, hotel=hotel,balance=0, wallet_id=wallet_id)
        
        return wallet_obj     
    
class Transactionserializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'transaction_id', 'transaction_type', 'created_at']
        read_only_fields = ['transaction_id', 'created_at']

    def create(self, validated_data):

        by_user = self.context['request'].user
        
        if not by_user.role == 'Admin': 
            raise serializers.ValidationError("Only admins can make transactions.")

        recipient_wallet = validated_data['wallet']
        recipient_user = recipient_wallet.user
        Transaction_type = validated_data['transaction_type']
  
        if Transaction_type=='Salary':
            Amount = User.objects.get(id = recipient_user.id).salary
        elif Transaction_type=='Bonus' or Transaction_type=='Expense' or Transaction_type=='Other':
            Amount = validated_data['amount']
        transaction_id = uuid.uuid4().hex[:12].upper()
        transaction_obj = Transaction.objects.create(wallet=recipient_wallet, amount=Amount, transaction_id=transaction_id, transaction_type=Transaction_type)
        recipient_wallet.balance += Amount
        recipient_wallet.save()
        return transaction_obj
 
