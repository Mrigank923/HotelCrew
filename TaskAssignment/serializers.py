from rest_framework import serializers
from .models import Task, TaskComment, Announcement
from hoteldetails.models import HotelDetails
from authentication.models import User, Manager, Staff, Receptionist
import random

class TaskSerializer(serializers.ModelSerializer):
    
    assigned_to = serializers.StringRelatedField(read_only=True)
    assigned_by = serializers.StringRelatedField(read_only=True)  
    
    class Meta:
        model = Task
        fields =[ 'title', 'description', 'created_at', 'updated_at', 'deadline','department', 'status', 'completed_at','assigned_by','assigned_to']
        read_only_fields = ('created_at', 'updated_at', 'completed_at')

    def validate(self, data):
        # Get the user from the context instead of data
        user = self.context['request'].user
        if(user.role == 'Admin'):
            hotel = HotelDetails.objects.get(user=user)
        elif(user.role == 'Manager'):
            manager = Manager.objects.get(user=user)
            hotel = manager.hotel
        elif(user.role == 'Receptionist'):
            receptionist = Receptionist.objects.get(user=user)
            hotel = receptionist.hotel
        else:
            raise serializers.ValidationError("Only Admin, Manager and Receptionist can assign tasks")
        data['hotel'] = hotel
        # Add assigned_by to data
        data['assigned_by'] = user
       # Check if hotel is provided
        if not hotel:
            raise serializers.ValidationError("Hotel information is required for task assignment.")
        # Validate assigner role
        if data['assigned_by'].role not in [ 'Admin','Manager', 'Receptionist']:
            raise serializers.ValidationError("Only Admin, Manager and Receptionist can assign tasks")
        
        # staff = Staff.objects.get(department=data['department'], hotel=hotel,is_avaliable=True)
        staff = Staff.objects.filter(department=data['department'], hotel=hotel,is_avaliable=True)
        if not staff.exists():
            staff = Staff.objects.filter(hotel=hotel,department=data['department'])
            if not staff.exists():
                raise serializers.ValidationError("No staff in the specified department.")
            n = staff.count()
            x= random.randint(0,n-1)
            data['assigned_to'] = staff[x]
        else:
            n = staff.count()
            x= random.randint(0,n-1)
            data['assigned_to'] = staff[x]
       
        data['assigned_to'].is_avaliable = False

        return data

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        validated_data['assigned_to'] = validated_data.pop('assigned_to', None)

        return super().create(validated_data)

    

class AnnouncementSerializer(serializers.ModelSerializer):
    assigned_to = serializers.StringRelatedField(many=True, read_only=True)
    assigned_by = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'description', 'created_at', 'assigned_to',
            'assigned_by', 'department', 'hotel', 'urgency'
        ]

class AnnouncementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = [
            'title', 'description', 'department', 'urgency'
        ]

    def create(self, validated_data):
        # Get the request context
        request = self.context.get('request')
        
        # Extract the department from the input
        department = validated_data.get('department')

        # Get staff members assigned to the provided department
        if request.user.role == 'Admin':
            hotel = HotelDetails.objects.get(user=request.user)
        elif request.user.role == 'Manager':
            manager = Manager.objects.get(user=request.user)
            hotel = manager.hotel
        if department == 'All':
            assigned_staff = Staff.objects.filter(hotel=hotel)
        elif department:
            assigned_staff = Staff.objects.filter(department=department)

        if not assigned_staff.exists():
            raise serializers.ValidationError(
                {"department": "No staff found in the specified department."}
            )

        # Add the 'assigned_to' and 'assigned_by' fields to the validated data
        validated_data['assigned_by'] = request.user
        validated_data['hotel'] = hotel
        validated_data['assigned_to'] = assigned_staff
        # Call the parent `create` method to save the announcement
        return super().create(validated_data)