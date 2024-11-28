from django.db import models
from authentication.models import User
from hoteldetails.models import HotelDetails
# Create your models here.
class wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey(HotelDetails, on_delete=models.CASCADE)
    balance = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    wallet_id = models.CharField(max_length=100, unique=True)
    

    def __str__(self):
        return f"{self.user} - {self.hotel.hotel_name} - {self.balance}"
    
PAYMENT_TYPE = [
    ('Salary', 'Salary'),
    ('Expense', 'Expense'),
    ('Bonus', 'Bonus'),
    ('Other', 'Other')
]
class Transaction(models.Model):
    wallet = models.ForeignKey(wallet, on_delete=models.CASCADE)
    amount = models.FloatField()
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(choices=PAYMENT_TYPE ,max_length=100, default='Salary')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.wallet} - {self.amount} - {self.transaction_type}"