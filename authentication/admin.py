from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id','email', 'user_name', 'role', 'is_staff', 'is_active', 'date_joined', 'last_login', 'upi_id', 'salary', 'user_profile')
    search_fields = ('email', 'user_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('user_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_name', 'password1', 'password2', 'role'),
        }),
    )

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'hotel')
    search_fields = ('user__email', 'user__user_name', 'hotel__name')
    list_filter = ('hotel',)

@admin.register(Receptionist)
class ReceptionistAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'hotel')
    search_fields = ('user__email', 'user__user_name', 'hotel__name')
    list_filter = ('hotel',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'hotel', 'department','shift')
    search_fields = ('user__email', 'user__user_name', 'hotel__name', 'department__name')
    list_filter = ('hotel', 'department')

@admin.register(EmailOTP)
class EmailOTPModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'otp_created_at', 'forgot')
    search_fields = ('email',)
    ordering = ('email',)

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'fcm_token')
    search_fields = ('user__email', 'fcm_token')
    ordering = ('user__email',)