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

class AttendanceListView(ListAPIView):
     permission_classes = [IsManagerOrAdmin]

     def get(self, request):
        today = timezone.now().date()
        # user_hotel
        user = request.user
        try:
            if user.role == 'Admin':
                return Response({'error': 'Admins cannot have attendance records.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user = Manager.objects.get(user=user)
                user_hotel = user.hotel
           
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
            user = User.objects.get(id=user_id)
            if user.role == 'Admin':
                return Response({'error': 'Admins cannot have attendance records.'}, status=status.HTTP_400_BAD_REQUEST)

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
                'user': user.username,
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
          
            user_hotel = HotelDetails.objects.get(user=request.user)
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        past_7_days = [today - timedelta(days=i) for i in range(7)]
        past_7_days.reverse()

        try:
            user_hotel = HotelDetails.objects.get(user=request.user)
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
            leave = Leave.objects.filter(user__in=non_admin_users, from_date=day, status='Approved').count()
            dates.append(day)
            total_crew_present.append(present)
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
                'message': 'From date, to date,description and leave type are required.'
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
            user_hotel = HotelDetails.objects.get(user=request.user)
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

        try:
            date = timezone.datetime.fromisoformat(str(date)).date()
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid date format.'
            }, status=status.HTTP_400_BAD_REQUEST)

        leave_count = Leave.LeaveCount(date)

        return Response({
            'status': 'success',
            'message': f"Total staff/receptionist on leave for {date}: {leave_count}",
            'data': {'leave_count': leave_count}
        }, status=status.HTTP_200_OK)
