from rest_framework import serializers
from authentication.models import User, Staff
from hoteldetails.models import HotelDetails,RoomType

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
        
class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['room_type', 'count', 'price']
        
class HotelUpdateSerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True)

    class Meta:
        model = HotelDetails
        fields = [
            'hotel_name',
            'legal_business_name',
            'year_established',
            'license_registration_numbers',
            'complete_address',
            'main_phone_number',
            'emergency_phone_number',
            'email_address',
            'total_number_of_rooms',
            'number_of_floors',
            'valet_parking_available',
            'valet_parking_capacity',
            'check_in_time',
            'check_out_time',
            'payment_methods',
            'room_price',
            'number_of_departments',
            'department_names',
            'room_types',
        ]

    def update(self, instance, validated_data):
        room_types_data = validated_data.pop('room_types', None)
        if room_types_data:
            instance.room_types.all().delete()
            for room_type_data in room_types_data:
                RoomType.objects.create(hotel=instance, **room_type_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
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
        
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_name','user_profile']
        
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