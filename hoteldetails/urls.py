from django.urls import path
from .views import *

urlpatterns = [
    path('register/', HotelDetailView.as_view(), name='hotelRegister'),
    path('book/',CheckinCustomerView.as_view(),name='bookroom'),
    path('checkout/<int:customer_id>/',CheckoutCustomerView.as_view(),name='checkout'),
    path('room-stats/',RoomStatsView.as_view(),name='stats'),
    path('all-customers/',CurrentCustomersView.as_view(),name='customer-list'),
    path('all-rooms/', DailyRoomsOccupiedView.as_view(), name='room-list'),
]