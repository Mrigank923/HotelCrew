from rest_framework import serializers
from .models import *

class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['room_type', 'count']

class HotelSerializer(serializers.ModelSerializer):
    room_types = RoomTypeSerializer(many=True, required=False)

    class Meta:
        model = HotelDetails
        fields = [
            'user', 'hotel_name', 'legal_business_name', 'year_established', 
            'license_registration_numbers', 'complete_address', 'main_phone_number',
            'emergency_phone_number', 'email_address', 'total_number_of_rooms', 
            'number_of_floors', 'valet_parking_available', 'valet_parking_capacity', 
            'check_in_time', 'check_out_time', 'payment_methods', 'room_price', 
            'number_of_departments', 'department_names', 'business_license', 
            'insurance_documents', 'room_types'
        ]

    def create(self, validated_data):
        room_types_data = validated_data.pop('room_types', [])
        hotel = HotelDetails.objects.create(**validated_data)
        for room_type_data in room_types_data:
            RoomType.objects.create(hotel=hotel, **room_type_data)
        return hotel