from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils.crypto import get_random_string
from .utils import send_registration_email
from hoteldetails.models import HotelDetails

class CustomUserManager(BaseUserManager):

    # for creating a normal user
    def create_user(self, email, user_name,role, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not user_name:
            raise ValueError('Username is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email,  user_name=user_name, role=role, **extra_fields)

        if role != 'Admin' :
        #    print("HI")
           password = get_random_string(12)

        user.set_password(password)
        user.save(using=self._db)
        send_registration_email_task.delay(email, password, role, user_name)
        return user

    def create_superuser(self, email, user_name, role='Admin',password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, user_name, role=role,password=password, **extra_fields)
    
class User(AbstractUser):

    ROLE_CHOICES = (
        ('Admin','Admin'),
        ('Manager','Manager'),
        ('Receptionist', 'Receptionist'),
        ('Staff', 'Staff')
    )

    username = None 
    email = models.EmailField(unique=True)
    user_name = models.CharField(max_length=150, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Admin')
    is_active = models.BooleanField(default=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    salary = models.IntegerField(default=0,blank=True,null=True)
    user_profile = models.ImageField(upload_to='', default='14-cd-campogalliano-web-1565969801.jpg', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
    
# class Department(models.Model):
#     ROLE_CHOICES = (
#         ('housekeeping','housekeeping'),
#         ('kitchen','kitchen'),
#         ('maintenance', 'maintenance'),
#         ('frontdesk', 'frontdesk')
#     )

#     name = models.CharField(max_length=40,choices=ROLE_CHOICES,default ='housekeeping')
   
#     def __str__(self):
#         return self.name

SHIFT_CHOICES = (
    ('Morning','Morning'),
    ('Evening','Evening'),
    ('Night', 'Night')
    )

class EmailOTP(models.Model):
   # user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='email_otp',null=True)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True )
    otp = models.IntegerField(null=True, blank=True)
    otp_created_at = models.DateTimeField(auto_now=True)
    user_name = models.CharField(max_length=150)  
    password = models.CharField(max_length=128)   
    forgot=models.BooleanField(default= False, blank= True)
    otp_verified = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f"{self.email} - OTP: {self.otp}"
    
    def is_otp_expired(self):
        expiration_time = self.otp_created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time
    
class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager_profile')
    hotel = models.ForeignKey(HotelDetails, on_delete=models.CASCADE, related_name='managers')
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='Morning')
    def __str__(self):
        return f"{self.user.email} ({self.user.role}) ({self.shift})"

class Receptionist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='receptionist_profile')
    hotel = models.ForeignKey(HotelDetails, on_delete=models.CASCADE, related_name='receptionists')
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='Morning')

    def __str__(self):
        return f"{self.user.email} ({self.user.role}) ({self.shift})"    

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    hotel = models.ForeignKey(HotelDetails, on_delete=models.CASCADE, related_name='staff')
    department=models.CharField(max_length=40)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='Morning')
    is_avaliable = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} ({self.user.role}) ({self.department}) ({self.shift})"
    