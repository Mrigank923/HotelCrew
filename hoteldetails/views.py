from rest_framework.generics import CreateAPIView
from .models import *
from .serializers import *
from rest_framework.permissions import AllowAny,IsAuthenticated
from attendance.permissions import IsNonStaff
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from authentication.models import Staff, Manager,Receptionist,User
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.utils.timezone import now, timedelta
from django.db.models import Sum, Count
from datetime import timedelta



class HotelDetailView(CreateAPIView):
   queryset = HotelDetails.objects.all()
   serializer_class = HotelSerializer
   permission_classes = [AllowAny]

   def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'User must be authenticated.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            hotel = serializer.save()
            
            excel_file = request.FILES.get('staff_excel_sheet')
            
            if excel_file:
                try:
                    df = pd.read_excel(excel_file)

                    
                    for _, row in df.iterrows():
                        role = row.get('Role', 'Staff')  # Default to 'Staff' if not specified
                        email = row['Email']
                        name = row['Name']
                        department = row['department']  
                        salary=row['salary']
                        shift=row['shift']
                        upi_id=row['upi_id']


                        user=User.objects.create_user(
                            email=email,
                            user_name=name,
                            role=role,
                            salary=salary,
                            upi_id=upi_id
                        )
                        # department = Department.objects.create(
                        #     name=sub_role,
                        # )
                        # Check the role and create the appropriate user
                        if role.lower() == 'manager':
                            manager = Manager.objects.create(
                                user=user,
                                # email=user.email,
                                # name=user.user_name,
                                hotel=hotel,
                                shift=shift.capitalize(),
                            )
                            
                        elif role.lower()=='receptionist':
                            receptionist=Receptionist.objects.create(
                                user=user,
                                # email=user.email,
                                # name=user.user_name,
                                hotel=hotel,
                                shift=shift.capitalize(),
                            )
                        else:  # For staff
                            staff = Staff.objects.create(
                                user=user,
                                # email=user.email,
                                # name=user.user_name,
                                hotel=hotel,
                                department = department.capitalize(),
                                shift=shift.capitalize(),
                            )

                except Exception as e:
                    return Response({
                        'status': 'error',
                        'message': f"Error processing Excel file: {str(e)}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            return Response({
                'status': 'success',
                'message': 'Hotel registered successfully',
                'hotel': serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class CheckinCustomerView(APIView):
    
    permission_classes = [IsNonStaff]
    
    def post(self, request):
        
        try:
            hotel = HotelDetails.objects.get(user=request.user)
        except HotelDetails.DoesNotExist:
            return Response({"error": "No hotel associated with the current user."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        room_type = data.get('room_type')
        # check_in = data.get('check_in_time')
        check_out = data.get('check_out_time')

        if not room_type or not check_out:
            return Response({
                'status': 'error',
                'message': 'Room type, check-in time, and check-out time are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_in_time = timezone.now()
            check_out_time = timezone.make_aware(timezone.datetime.fromisoformat(check_out))


            if check_in_time >= check_out_time:
                return Response({
                    'status': 'error',
                    'message': 'Check-out time must be after check-in time.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # customers_to_release = Customer.objects.filter(
            #     Q(room_released=False) & Q(check_out_time__lte=timezone.now())
            # )
            
            # # Release rooms for these customers
            # for customer in customers_to_release:
            #     customer.save()


            room = RoomType.objects.get(room_type=room_type)
            

            if room.count <= 0:
                return Response({
                    'status': 'error',
                    'message': f"No {room_type} rooms available."
                }, status=status.HTTP_404_NOT_FOUND)
                
            stay_duration = (check_out_time - check_in_time).days+1
            
            print(stay_duration)
            
            room.count -= 1
            room.save()

            customer = Customer.objects.create(
                hotel=hotel,
                name=data.get('name'),
                phone_number=data.get('phone_number'),
                email=data.get('email'),
                check_in_time=check_in_time,
                check_out_time=check_out_time,
                room_no=room.count+1,
                room=room,
                price=room.price*stay_duration,
                status=data.get('status')
            )


            serializer = CustomerSerializer(customer)
            return Response({
                'status': 'success',
                'message': f"Room booked successfully!",
                'room_available':room.count,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        except RoomType.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f"Room type '{room_type}' does not exist."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class CurrentCustomersView(ListAPIView):
    permission_classes =[IsNonStaff]
    serializer_class = CustomerSerializer
    pagination_class = None
    def get_queryset(self):
        try:
            hotel = HotelDetails.objects.get(user=self.request.user)
        except HotelDetails.DoesNotExist:
            return Customer.objects.none()
        
        return Customer.objects.filter(checked_out=False,hotel=hotel)
            
            
class CheckoutCustomerView(APIView):
    permission_classes = [IsNonStaff]
    
    def post(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        current_time = timezone.now()

        check_in_time = customer.check_in_time
        original_check_out_time = customer.check_out_time or current_time
        
        if customer.checked_out==True:
            return Response({
                "message":"customer already checked out",
                "final_price": customer.price,
                "room_available":customer.room.count
            },status=status.HTTP_200_OK)

        if current_time > original_check_out_time:
            stay_duration = (current_time.date() - check_in_time.date()).days + 1 
        else:
            stay_duration = (original_check_out_time.date() - check_in_time.date()).days + 1

        # Recalculate price
        customer.price = customer.room.price * stay_duration

        customer.checkout_time = current_time
        customer.checked_out = True

        customer.room.count += 1
        customer.room.save()
        customer.save()

        return Response({
            "message": "Customer checked out successfully",
            "stay_duration_days": stay_duration,
            "final_price": customer.price,
            "room_available":customer.room.count
        }, status=status.HTTP_200_OK)
        
        
class RoomStatsView(APIView):
    permission_classes = [IsNonStaff]

    def get(self, request):

        try:
            hotel = HotelDetails.objects.get(user=request.user)
        except HotelDetails.DoesNotExist:
            return Response({"error": "No hotel associated with the current user."}, status=status.HTTP_400_BAD_REQUEST)

        today = now().date()
        dates = [(today - timedelta(days=i)) for i in range(7)]
        dates.reverse()  

        checkins = []
        checkouts = []
        revenues = []

        for date in dates:

            daily_checkins = Customer.objects.filter(
                hotel=hotel,
                check_in_time__date=date
            ).count()
            checkins.append(daily_checkins)

            daily_checkouts = Customer.objects.filter(
                hotel=hotel,
                check_out_time__date=date
            ).count()
            checkouts.append(daily_checkouts)

            daily_revenue = Customer.objects.filter(
                hotel=hotel,
                check_out_time__date=date
            ).aggregate(total_revenue=Sum('price'))['total_revenue'] or 0
            revenues.append(daily_revenue)

        return Response({
            "dates": [date.strftime("%Y-%m-%d") for date in dates],
            "daily_checkins": checkins,
            "daily_checkouts": checkouts,
            "daily_revenues": revenues
        }, status=status.HTTP_200_OK)
    

class DailyRoomsOccupiedView(APIView):
    permission_classes = [IsNonStaff]

    def get(self, request):
    
        try:
            user=request.user
            if user.role=='Manager':
               user = Manager.objects.get(user =user)
               hotel = user.hotel
            elif user.role=='Receptionist':
                user = Receptionist.objects.get(user=user)
                hotel = user.hotel
            elif user.role=='Admin':
                hotel = HotelDetails.objects.get(user=user)

        except HotelDetails.DoesNotExist:
            return Response({"error": "No hotel associated with the current user."}, status=status.HTTP_400_BAD_REQUEST)

        today = now().date()
        
        rooms_occupied_today = Customer.objects.filter(
                hotel=hotel,
                checked_out=False,
            ).count()
        available_rooms = RoomType.objects.filter(hotel=hotel).aggregate(available_rooms=Sum('count'))['available_rooms']

        return Response({
            "rooms_occupied": rooms_occupied_today,
            "available_rooms": available_rooms,
        }, status=status.HTTP_200_OK)

def hotelname(user):
    if user.role=='Manager':
        user = Manager.objects.get(user =user)
        hotel = user.hotel
    elif user.role=='Receptionist':
        user = Receptionist.objects.get(user=user)
        hotel = user.hotel
    elif user.role=='Admin':
        hotel = HotelDetails.objects.get(user=user)
    elif user.role=='Staff':
        user = Staff.objects.get(user=user)
        hotel = user.hotel
    return hotel    