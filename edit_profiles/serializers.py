from rest_framework import serializers
from authentication.models import User
from hoteldetails.models import HotelDetails

from django.utils import timezone

        
class StaffListSerializer(serializers.ModelSerializer):
    
    department = serializers.SerializerMethodField()
    shift= serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_name','email', 'role','department','salary','upi_id','shift']

    def get_department(self, obj):
        if obj.role == 'Staff':
            try:
                return obj.staff_profile.department
            except Staff.DoesNotExist:
                return None
        return None
    
    def get_shift(self, obj):
        if obj.role == 'Staff':
            return obj.staff_profile.shift
        elif obj.role== 'Manager':
            return obj.manager_profile.shift
        else:
            return obj.receptionist_profile.shift
    
class UserSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    department = serializers.CharField(required=False)
    upi_id = serializers.CharField(required=False)
    salary = serializers.IntegerField(required=False)
    shift = serializers.ChoiceField(choices=['Morning', 'Evening', 'Night'], required=False)

    class Meta:
        model = User
        fields = ['id', 'user_name', 'email', 'role', 'department','salary','upi_id','shift']
        
class HotelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelDetails
        exclude = ['user']
        
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_name','user_profile']

class ProfileViewSerializer(serializers.ModelSerializer):

    department = serializers.SerializerMethodField()
    shift= serializers.SerializerMethodField()    

    class Meta:
        model = User
        fields = ['id','department','shift','user_name','email','role','salary','user_profile']
        
    def get_department(self, obj):
        if obj.role == 'Staff':
            try:
                return obj.staff_profile.department
            except Staff.DoesNotExist:
                return None
        return obj.role
    
    def get_shift(self, obj):
        if obj.role == 'Staff':
            return obj.staff_profile.shift
        elif obj.role== 'Manager':
            return obj.manager_profile.shift
        elif obj.role=='Receptionist':
            return obj.receptionist_profile.shift
        return obj.role
        
class ScheduleListSerializer(serializers.ModelSerializer):
    
    department = serializers.SerializerMethodField()
    shift= serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_name','department','shift']

    def get_department(self, obj):
        if obj.role == 'Staff':
            try:
                return obj.staff_profile.department
            except Staff.DoesNotExist:
                return None
        return obj.role
    
    def get_shift(self, obj):
        if obj.role == 'Staff':
            return obj.staff_profile.shift
        elif obj.role== 'Manager':
            return obj.manager_profile.shift
        else:
            return obj.receptionist_profile.shift