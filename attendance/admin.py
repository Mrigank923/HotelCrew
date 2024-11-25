from django.contrib import admin
from .models import Attendance,Leave

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'attendance')
    list_filter = ('attendance', 'date', 'user')
    search_fields = ('user__email',)
    ordering = ('-date',)
    
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'from_date', 'status')
    list_filter = ('status', 'from_date', 'user')
    search_fields = ('user__email',)
    ordering = ('-from_date',)