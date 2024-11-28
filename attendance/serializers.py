from rest_framework import serializers
from authentication.models import User, Staff
from .models import Attendance,Leave
from django.utils import timezone

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['date', 'attendance']
        
class AttendanceListSerializer(serializers.ModelSerializer):
    current_attendance = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    shift = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_name', 'email', 'role','department','current_attendance','user_profile','shift']

    def get_current_attendance(self, obj):
        today = timezone.now().date()
        attendance = Attendance.objects.filter(user=obj, date=today).first()
        return 'Present' if attendance and attendance.attendance else 'Absent'
    
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

class LeaveSerializer(serializers.ModelSerializer):
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Leave
        fields = ['id','user_name','from_date', 'to_date', 'leave_type','reason','duration', 'status']
        
    def get_user_name(self,obj):
        return obj.user.user_name