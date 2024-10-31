from rest_framework import serializers,status
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework.response import Response
from django.core.validators import MinLengthValidator
from .utils import *
import random
from .models import EmailOTP, User

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'first_name', 'last_name','phone_number')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        phone_otp = PhoneOTP.objects.filter(phone_number=attrs['phone_number']).first()
        if not phone_otp or not phone_otp.otp: 
            raise serializers.ValidationError({"phone_number": "OTP not sent or invalid."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ForgetPassSerializer(serializers.Serializer):
     email = serializers.EmailField(write_only=True)

     def validate(self, data):
       user= User.objects.filter(email=data['email']).exists()
       if not user:
           raise serializers.ValidationError({"error":"User doesn't exist"})
       otpto= self.sendotp(data)
       EmailOTP.objects.update_or_create(
            email= data['email'],
            defaults={'otp':otpto,'forgot' :True}
        )
       return data
        
     def sendotp(self, attrs):
        otpto = random.randint(1000, 9999)
        otp_for_reset(attrs['email'], otpto)
        
        return otpto
     
class VerifyOTPSerializer(serializers.Serializer):
    email= serializers.CharField()
    otp = serializers.IntegerField()

    def validate(self, data):
        try:
          user= EmailOTP.objects.get(email= data['email'])
        except:
          raise serializers.ValidationError({'error':'Invalid user'})
        user= EmailOTP.objects.get(email= data['email'])
        otph = user.otp
        print(otph)
        if otph != data['otp']:
            raise serializers.ValidationError({'error':'Invalid OTP'})
        if user.forgot:
            self.forgot_us(data)
        else:
            self.create_us(data)
        return {
            "message" : "verified" }
        
    
    def forgot_us(self , data):
        EmailOTP.objects.filter(email=data['email']).delete()
        return{
            'message' : 'User verified successfully'
        }
    
class ResetPassSerializer(serializers.Serializer):
     email= serializers.EmailField()
     new_password = serializers.CharField(min_length=8)
     confirm_password = serializers.CharField(min_length=8)

     def validate(self, attrs):
        if attrs['new_password'] is None:
           raise serializers.ValidationError({"password": "Password should not be blank"})
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        try:
          user = User.objects.get(email=attrs['email'])
        except:
            raise serializers.ValidationError({"error": "User with this email does not exist."})
        attrs['user']=user
        return attrs
        
     def save(self):
            user = self.validated_data['user']
            user.set_password(self.validated_data['new_password'])
            user.save()
            return user 
        
        
        
class VerifyPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.IntegerField()

    def validate(self, data):
        try:
            otp_instance = PhoneOTP.objects.get(phone_number=data['phone_number'])
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError({"phone_number": "Phone number not found."})

        if otp_instance.otp != data['otp']:
            raise serializers.ValidationError({"otp": "Invalid OTP"})
        return data