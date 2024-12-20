from itertools import chain
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import status
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from django.utils import timezone
from datetime import date,timedelta
from authentication.models import User,Manager,Receptionist,Staff
from hoteldetails.models import HotelDetails
from .models import Attendance,Leave
from .serializers import AttendanceListSerializer,LeaveSerializer,AttendanceSerializer
from .permissions import IsManagerOrAdmin,IsNonAdmin
from hoteldetails.utils import get_hotel
from TaskAssignment.permissions import IsAdminorManagerOrReceptionist
from django.db.models import Q
from dateutil.parser import parse as parse_date


class AttendanceListView(ListAPIView):
     permission_classes = [IsManagerOrAdmin]

     def get(self, request):
        today = timezone.now().date()
        # user_hotel
        user = request.user
        try:
            user_hotel =get_hotel(user)
            if not user_hotel:
               return Response({"error": "Hotel not found"}, status=404)
          
            # print("hi")
        except HotelDetails.DoesNotExist:
            return Response(
                {'error': 'No hotel is associated with you!.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # non_admin_users = User.objects.exclude(role='Admin').filter(hotel=user_hotel)
        managers=Manager.objects.filter(hotel=user_hotel)
        staffs=Staff.objects.filter(hotel=user_hotel)
        receptionists=Receptionist.objects.filter(hotel=user_hotel)
        
        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))
        
        if not Attendance.objects.filter(date=today,user__in=non_admin_users).exists():
            
            # non_admin_users = User.objects.exclude(role='Admin').filter(hotel=user_hotel)

            Attendance.objects.bulk_create([
                Attendance(user=user, date=today, attendance=False) 
                for user in non_admin_users
            ])
            
        serializer = AttendanceListSerializer(non_admin_users, many=True, context={'date': today})
        return Response(serializer.data, status=200)

class ChangeAttendanceView(APIView):
    permission_classes = [IsManagerOrAdmin]
    def post(self, request, user_id):
        try:

            adminORmanager = request.user
            hotel = get_hotel(adminORmanager)
            if not hotel:
               return Response({"error": "you do not have a Hotel"}, status=404)
            
            user = User.objects.get(id=user_id)
            if user.role == 'Admin':
                return Response({'error': 'Admins cannot have attendance records.'}, status=status.HTTP_400_BAD_REQUEST)
            
            userHotel = get_hotel(user)
            if not userHotel:
               return Response({"error": "staff Hotel not found"}, status=404)
            
            if userHotel != hotel:
                return Response({'error': 'User not found in your hotel.'}, status=status.HTTP_404_NOT_FOUND)
            
            
            date_today = timezone.now().date()
            attendance, created = Attendance.objects.get_or_create(
                user=user,
                date=date_today
            )
            
            attendance.attendance = not attendance.attendance
            attendance.save()
            
            return Response(
                {
                    'message': f'Attendance for {user.user_name} on {date_today} set to {"Present" if attendance.attendance else "Absent"}.',
                    'attendance': attendance.attendance
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response({'error': 'User does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class CheckAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        
        date_str = request.query_params.get('date')
        
        if date_str:
            try:
                date_t = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date_t = timezone.now().date()

        try:
            attendance = Attendance.objects.get(user=user, date=date_t)
            
            attendance_status = "Present" if attendance.attendance else "Absent"
            
            return Response({'date': date_t,'user': user.user_name,'attendance':
            attendance_status,},
                status=status.HTTP_200_OK
            )
        except Attendance.DoesNotExist:
            return Response({'message': f'No attendance record found for {date_t}'},
                status=status.HTTP_200_OK
            )
            
class StaffAttendanceView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)

        # Filter attendance records for the current month
        return Attendance.objects.filter(
            user=user,
            date__range=[first_day_of_current_month, today]
        ).order_by('date')
            
class MonthlyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)

        attendance_records = Attendance.objects.filter(
            user=user,
            date__range=[first_day_of_current_month, today],
            attendance=True
        )

        days_present = attendance_records.count()
        
        total_leave_days = Leave.objects.filter(
            user=user,
            status='Approved',
            from_date__gte=first_day_of_current_month,
            from_date__month=today.month,
            from_date__year=today.year
        ).aggregate(Sum('duration'))['duration__sum'] or 0

        return Response(
            {
                'user': user.user_name,
                'month': today.strftime("%B %Y"),
                'days_present': days_present,
                'leaves':total_leave_days,
                'total_days_up_to_today': today.day
            },
            status=status.HTTP_200_OK
        )


class AttendanceStatsView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        try:
            user_hotel = get_hotel(request.user)
            if not user_hotel:
               return Response({"error": "Hotel not found"}, status=404)
        except HotelDetails.DoesNotExist:
            return Response(
                {'error': 'No hotel is associated with you!.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        managers=Manager.objects.filter(hotel=user_hotel)
        staffs=Staff.objects.filter(hotel=user_hotel)
        receptionists=Receptionist.objects.filter(hotel=user_hotel)
        
        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))
        
        present = Attendance.objects.filter(
            user__in=non_admin_users,
            date=today,
            attendance=True
        )
        crew = Attendance.objects.filter(
            user__in=non_admin_users,
            date=today,
        )
        total_present=present.count()
        total_crew=crew.count()
        

        month_attendance = Attendance.objects.filter(
            user__in=non_admin_users,
            date__gte=current_month_start,
            date__lte=today
        )

        total_present_month = month_attendance.filter(attendance=True).count()

        total_working_days = month_attendance.values('date').distinct().count()
        
        return Response({
            'total_crew': total_crew,
            'total_present': total_present,
            'total_working_days': total_working_days,
            'total_present_month': total_present_month,
        }, status=status.HTTP_200_OK)

class AttendanceWeekStatsView(APIView):
    permission_classes = [IsAdminorManagerOrReceptionist]

    def get(self, request):
        today = timezone.now().date()
        past_7_days = [today - timedelta(days=i) for i in range(7)]
        past_7_days.reverse()

        try:
            user_hotel = get_hotel(request.user)
            if not user_hotel:
               return Response({"error": "Hotel not found"}, status=404)
        except HotelDetails.DoesNotExist:
            return Response(
                {'error': 'No hotel is associated with the authenticated user.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        managers = Manager.objects.filter(hotel=user_hotel)
        staffs = Staff.objects.filter(hotel=user_hotel)
        receptionists = Receptionist.objects.filter(hotel=user_hotel)

        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))

        dates = []
        total_crew_present = []
        total_staff_absent = []
        total_crew_leave =[]

        for day in past_7_days:
            present = Attendance.objects.filter(user__in=non_admin_users, date=day, attendance=True).count()
            crew = Attendance.objects.filter(user__in=non_admin_users, date=day).count()
            leave = Leave.objects.filter(user__in=non_admin_users, from_date=day,to_date=day, status='Approved').count()
            dates.append(day)
            total_crew_present.append(present-leave)
            total_staff_absent.append(crew - present-leave)
            total_crew_leave.append(leave)

        return Response({
            'dates': dates,
            'total_crew_present': total_crew_present,
            'total_staff_absent': total_staff_absent,
            'total_leave': total_crew_leave
        }, status=status.HTTP_200_OK)
        
class ApplyLeaveView(APIView):
    permission_classes= [IsNonAdmin]
    
    def get(self, request):
        user = request.user
        leaves = Leave.objects.filter(user=user)
        serializer = LeaveSerializer(leaves, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        
        data = request.data
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        leave_type = data.get('leave_type')
        reason = data.get('reason')

        if not from_date or not to_date or not leave_type or not reason:
            return Response({
                'status': 'error',
                'message': 'from_date, to_date, description and leave_type are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from_date_obj = parse_date(from_date).date()
            to_date_obj = parse_date(to_date).date()

        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid date format. Please provide ISO format dates.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if from_date_obj < timezone.now().date():
            return Response({
                'status': 'error',
                'message': 'From date cannot be in the past.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if from_date_obj > to_date_obj:
            return Response({
                'status': 'error',
                'message': 'From date cannot be greater than to date.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        overlapping_leave = Leave.objects.filter(
            user= user,
            from_date__lte = to_date_obj,
            to_date__gte = from_date_obj

        )

        if overlapping_leave.exists():
            return Response({
                'status':'error',
                'message':'user already have a leave applied for this date rannge'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            leave = Leave.objects.create(
                user=user,
                from_date=timezone.datetime.fromisoformat(from_date).date(),
                to_date=timezone.datetime.fromisoformat(to_date).date(),
                leave_type=leave_type,
                reason=reason
            )
            return Response({
                'status': 'success',
                'message': 'Leave request submitted successfully.',
                'data': LeaveSerializer(leave).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeaveRequestListView(APIView):
    
    permission_classes=[IsManagerOrAdmin]

    def get(self, request):

        try:
            user_hotel = get_hotel(request.user)
            if not user_hotel:
               return Response({"error": "Hotel not found"}, status=404)
        except HotelDetails.DoesNotExist:
            return Response(
                {'error': 'No hotel is associated with the authenticated user.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        managers = Manager.objects.filter(hotel=user_hotel)
        staffs = Staff.objects.filter(hotel=user_hotel)
        receptionists = Receptionist.objects.filter(hotel=user_hotel)

        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))
            
        pending_leaves = Leave.objects.filter(
            user__in=non_admin_users,
            status='Pending'
        ).order_by('from_date')

        serializer = LeaveSerializer(pending_leaves, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
        
class ApproveLeaveView(APIView):
    
    permission_classes=[IsManagerOrAdmin]
    
    def patch(self, request, leave_id):

        if not request.data.get('status'):
            return Response({
                'status': 'error',
                'message': 'Status is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.data.get('status') not in ['Approved', 'Rejected']:
            return Response({
                'status': 'error',
                'message': 'Invalid status. Status must be either Approved or Rejected.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        hotel = get_hotel(request.user)
        if not hotel:
            return Response({
                'status': 'error',
                'message': 'Hotel not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        staff = Leave.objects.get(id=leave_id).user
        hotel_staff = get_hotel(staff)

        if hotel_staff != hotel:
            return Response({
                'status': 'error',
                'message': 'Staff not found in your hotel.'
            }, status=status.HTTP_404_NOT_FOUND)
        

        try:
            leave = Leave.objects.get(id=leave_id,status='Pending')
            leave.status = request.data.get('status')
            leave.save()

            return Response({
                'status': 'success',
                'message': f"Leave request for {leave.user} updated to {leave.status}."
            }, status=status.HTTP_200_OK)

        except Leave.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Leave request not found or already processed.'
            }, status=status.HTTP_404_NOT_FOUND)

class LeaveCountView(APIView):
    def get(self, request):
        date = request.query_params.get('date', timezone.now().date())

        hotel = get_hotel(request.user)
        if not hotel:
            return Response({
                'status': 'error',
                'message': 'Hotel not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            date = timezone.datetime.fromisoformat(str(date)).date()
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid date format.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        users_in_hotel = User.objects.filter(
            Q(manager_profile__hotel=hotel) |
            Q(receptionist_profile__hotel=hotel) |
            Q(staff_profile__hotel=hotel)
        )

        leave_count = Leave.objects.filter(
            user__in=users_in_hotel,
            status='Approved',
            from_date__lte=date,
            to_date__gte=date
        ).count()

        return Response({
            'status': 'success',
            'message': f"Total staff/receptionist on leave for {date}: {leave_count}",
            'data': {'leave_count': leave_count}
        }, status=status.HTTP_200_OK)
