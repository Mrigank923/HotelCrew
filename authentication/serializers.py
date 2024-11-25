from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework.response import Response
from .utils import *
import random
from .models import *
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.core.validators import MinLengthValidator, EmailValidator
from django.contrib.auth.password_validation import validate_password
from .tasks import send_otp_for_register_task
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password], style={'input_type': 'password'})
    email = serializers.EmailField(validators=[EmailValidator()])
    
    class Meta:
        model = User
        fields = ['id', 'email', 'user_name', 'role', 'password', 'created_at', 'updated_at', 'is_active', 'upi_id', 'salary', 'user_profile']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'user_name': {'required': True, 'min_length': 3},
            'role': {'required': True}
        }

    def validate_email(self, value):
        """Validate email uniqueness case-insensitively."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        role = validated_data.get('role', 'Admin')
        if role == 'Admin' and 'password' not in validated_data:
            raise serializers.ValidationError({"password": "Password is required for Admin users"})
        
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            raise serializers.ValidationError(str(e))
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        if 'email' in validated_data:
            # Check email uniqueness excluding current user
            if User.objects.filter(email__iexact=validated_data['email']).exclude(id=instance.id).exists():
                raise serializers.ValidationError({"email": "User with this email already exists."})
        return super().update(instance, validated_data)

# class EmailOTPSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EmailOTP
#         fields = ['email', 'user_name', 'otp', 'otp_verified', 'forgot']
#         read_only_fields = ['otp', 'otp_verified']

class ManagerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Manager
        fields = ['id', 'user', 'hotel','shift']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'Manager'
        user = User.objects.create_user(**user_data)
        manager = Manager.objects.create(user=user, **validated_data)
        return manager

class ReceptionistSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Receptionist
        fields = ['id', 'user', 'hotel', 'shift']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'Receptionist'
        user = User.objects.create_user(**user_data)
        receptionist = Receptionist.objects.create(user=user, **validated_data)
        return receptionist

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Staff
        fields = ['id', 'user', 'hotel', 'department', 'shift','is_available']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'Staff'
        user = User.objects.create_user(**user_data)
        staff = Staff.objects.create(user=user, **validated_data)
        return staff


class RegistrationOTPSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return data

    def save(self):
        email = self.validated_data['email']
        user_name = self.validated_data['user_name']
        password = self.validated_data['password']
   
        otp = random.randint(1000, 9999)

        send_otp_for_register_task.delay(user_name, email, otp)
        EmailOTP.objects.update_or_create(email=email, defaults={'otp': otp, 'user_name': user_name, 'password': password})
        
        return {'message': 'OTP sent successfully'}

class RegisterWithOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()
    
    def validate(self, data):
       
        try:
            otp_record = EmailOTP.objects.get(email=data['email'])
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({'error': 'OTP not found or invalid user'})
       
        if otp_record.otp != data['otp']:
            raise serializers.ValidationError({'error': 'Invalid OTP'})
        

        if otp_record.is_otp_expired():
            raise serializers.ValidationError({'error': 'OTP expired'})
        

        return data

    def save(self, **kwargs):
        email = self.validated_data['email']
        otp_record = EmailOTP.objects.get(email=email)
        user_name = otp_record.user_name
        password = otp_record.password

        user = User.objects.create_user(
            email=email,
            user_name=user_name,
            password=password,
            role='Admin'
        )

        otp_record.delete()

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ForgetPassSerializer(serializers.Serializer):
     email = serializers.EmailField(write_only=True)

     def validate(self, data):
       user= User.objects.filter(email=data['email']).exists()
       if not user:
           raise serializers.ValidationError({"error":"User doesn't exist"})
       otp_entry, created = EmailOTP.objects.get_or_create(email=data['email'])
        
       if not created and otp_entry.otp_created_at:
            time_since_last_otp = timezone.now() - otp_entry.otp_created_at
            if time_since_last_otp < timedelta(seconds=30):
                raise serializers.ValidationError({"error": "Please wait 30 seconds before requesting a new OTP."})

       if not created and otp_entry.is_otp_expired():
            otp_entry.otp = None  

       otpto = self.sendotp(data)
        
       otp_entry.otp = otpto
       otp_entry.forgot = True
       otp_entry.otp_created_at = timezone.now()
       otp_entry.otp_verified = False
       otp_entry.save()
       return data
        
     def sendotp(self, attrs):
        otpto = random.randint(1000, 9999)
        send_otp_for_reset_task.delay(attrs['email'], otp)
        
        return otpto
     
class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()

    def validate(self, data):
        try:
            otp_record = EmailOTP.objects.get(email=data['email'], forgot=True)
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({'error': 'OTP not found or invalid user'})

        if otp_record.otp != data['otp']:
            raise serializers.ValidationError({'error': 'Invalid OTP'})
        if otp_record.is_otp_expired():
            raise serializers.ValidationError({'error': 'OTP expired'})

        data['otp_record'] = otp_record
        return data

    def save(self):
        otp_record = self.validated_data['otp_record']
        otp_record.otp_verified = True 
        otp_record.save()
        return {'message': 'OTP verified successfully'}

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=8, write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        try:
            otp_record = EmailOTP.objects.get(email=data['email'], otp_verified=True)
            user = User.objects.get(email=data['email'])
        except (EmailOTP.DoesNotExist, User.DoesNotExist):
            raise serializers.ValidationError({"error": "OTP verification required or user does not exist."})

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        
        
        EmailOTP.objects.filter(email=self.validated_data['email']).delete()  

        return {'message': 'Password reset successfully'}
