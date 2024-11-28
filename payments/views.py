from .models import wallet, Transaction
from rest_framework.views import APIView
from .serializers import walletserializer, Transactionserializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from attendance.permissions import *

class walletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallets = wallet.objects.filter(user=request.user)
        serializer = walletserializer(wallets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if wallet.objects.filter(user=request.user).exists():
            return Response({'message': 'Wallet already exists'}, status=status.HTTP_200_OK)
        serializer = walletserializer(data={}, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MakeTransactionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = Transactionserializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transaction = Transaction.objects.filter(wallet__user=request.user)
        serializer = Transactionserializer(transaction, many=True)
        return Response(serializer.data)