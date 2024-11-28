from django.urls import path
from .views import WeeklyHotelPerformanceView, WeeklyStaffPerformanceView, WeeklyFinanceView

urlpatterns = [
    path('performance/hotel/week/', WeeklyHotelPerformanceView.as_view(), name='hotel-performance-weekly'),
    path('performance/staff/week/', WeeklyStaffPerformanceView.as_view(), name='staff-performance-monthly'),
    path('finance/week/', WeeklyFinanceView.as_view(), name='finance-monthly'),
]
