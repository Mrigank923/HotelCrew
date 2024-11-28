from django.urls import path
from .views import *

urlpatterns = [
    path('list/', StaffListView.as_view(), name='staff-list'),
    path('count/', RoleCountView.as_view(), name='staff-count'),
    path('create/',CreateCrewView.as_view(),name='staff-create'),
    path('mass-create/',MassCreateStaffView.as_view(),name='mass-create'),
    path('update/<int:user_id>/',UpdateCrewView.as_view(),name='staff-update'),
    path('delete/<int:user_id>/',DeleteCrewView.as_view(),name='staff-delete'),
    path('view_hoteldetails/',GetHotelDetailsView.as_view(),name='hotel-view'),
    path('hoteldetails/',UpdateHotelDetailsView.as_view(),name='hotel-update'),
    path('user_profile/',UpdateUserProfileView.as_view(),name='user_profile-update'),
    path('schedule_list/',ScheduleListView.as_view(),name='schedule-list'),
    path('schedule_change/<int:user_id>/',ChangeShiftView.as_view(),name='schedule-change'),
]