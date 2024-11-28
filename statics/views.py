from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from attendance.models import *
from .serializers import WeeklyHotelPerformanceSerializer, WeeklyStaffPerformanceSerializer, WeeklyFinanceSerializer
from datetime import timedelta
from django.utils.timezone import now
from attendance.permissions import *
from TaskAssignment.models import Task
from authentication.models import Staff
from attendance.models import Attendance, Leave
from hoteldetails.models import Customer
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.db.models import Sum

class WeeklyHotelPerformanceView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        user = request.user
        if user.role not in ['Admin', 'Manager']:
            return Response({"error": "You do not have permission to view this data."}, status=status.HTTP_403_FORBIDDEN)

        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  
        end_of_week = start_of_week + timedelta(days=6)  
       
        attendance_data = (
            Attendance.objects.filter(date__range=[start_of_week, end_of_week])
            .values('date')
            .annotate(present_count=Count('id', filter=Q(attendance=True)))
        )

        task_data = (
            Task.objects.filter(created_at__date__range=[start_of_week, end_of_week])
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                tasks_completed=Count('id', filter=Q(status='Completed')),
                tasks_assigned=Count('id'),
            )
        )

        leave_data = Leave.objects.filter(
            from_date__lte=end_of_week, to_date__gte=start_of_week
        )
        leave_lookup = {}
        for leave in leave_data:
            for single_date in (
                leave.from_date + timedelta(days=x)
                for x in range((leave.to_date - leave.from_date).days + 1)
            ):
                if start_of_week <= single_date <= end_of_week:
                    leave_lookup[single_date] = leave_lookup.get(single_date, 0) + 1

        # Convert queries to dictionaries for quick lookups
        attendance_lookup = {item['date']: item['present_count'] for item in attendance_data}
        task_lookup = {
            item['date']: {
                'tasks_completed': item['tasks_completed'],
                'tasks_assigned': item['tasks_assigned'],
            }
            for item in task_data
        }

        weekly_stats = []
        for single_date in (start_of_week + timedelta(days=x) for x in range(7)):
            staff_present = attendance_lookup.get(single_date, 0)
            staff_on_leave = leave_lookup.get(single_date, 0)
            tasks_completed = task_lookup.get(single_date, {}).get('tasks_completed', 0)
            tasks_assigned = task_lookup.get(single_date, {}).get('tasks_assigned', 0)

            performance_percentage = (
                ((staff_present / (staff_present + staff_on_leave)) if (staff_present + staff_on_leave) > 0 else 0)
                + (tasks_completed / tasks_assigned if tasks_assigned > 0 else 0)
            ) / 2 * 100

            weekly_stats.append({
                'date': single_date,
                'performance_percentage': performance_percentage,
            })

        data = {
            'week_range': f"{start_of_week} - {end_of_week}",
            'weekly_stats': weekly_stats,
        }
        serializer = WeeklyHotelPerformanceSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class WeeklyStaffPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user1 = request.user
        if user1.role != 'Staff':
            return Response({"error": "You do not have permission to view this data."}, status=status.HTTP_403_FORBIDDEN)

        user2 = Staff.objects.get(user=user1)

        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)

        # Pre-fetch data
        attendance_data = (
            Attendance.objects.filter(user=user1, date__range=[start_of_week, end_of_week])
            .values('date', 'attendance')
        )
        attendance_lookup = {item['date']: item['attendance'] for item in attendance_data}

        leave_data = (
            Leave.objects.filter(
                user=user1,
                from_date__lte=end_of_week,
                to_date__gte=start_of_week,
                status='Approved',
            )
        )
        leave_lookup = {}
        for leave in leave_data:
            for single_date in (
                leave.from_date + timedelta(days=x)
                for x in range((leave.to_date - leave.from_date).days + 1)
            ):
                if start_of_week <= single_date <= end_of_week:
                    leave_lookup[single_date] = True

        task_data = (
            Task.objects.filter(
                assigned_to=user2,
                created_at__date__range=[start_of_week, end_of_week],
            )
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                tasks_completed=Count('id', filter=Q(status='Completed')),
                tasks_assigned=Count('id'),
            )
        )
        task_lookup = {
            item['date']: {
                'tasks_completed': item['tasks_completed'],
                'tasks_assigned': item['tasks_assigned'],
            }
            for item in task_data
        }

        # Build the daily stats
        daily_stats = []
        for single_date in (start_of_week + timedelta(days=x) for x in range(7)):  # Iterate for 7 days in the week
            attendance_status = attendance_lookup.get(single_date)
            presence_status = (
                'Present' if attendance_status
                else 'Leave' if leave_lookup.get(single_date)
                else 'Absent'
            )

            tasks_completed = task_lookup.get(single_date, {}).get('tasks_completed', 0)
            tasks_assigned = task_lookup.get(single_date, {}).get('tasks_assigned', 0)

            performance_percentage = (
                (1 if presence_status == 'Present' else 0.5 if presence_status == 'Leave' else 0)
                + (tasks_completed / tasks_assigned if tasks_assigned > 0 else 0)
            ) * 50

            daily_stats.append({
                'date': single_date,
                'performance_percentage': performance_percentage,
            })

        data = {
            'week_range': f"{start_of_week} - {end_of_week}",
            'daily_stats': daily_stats,
        }
        serializer = WeeklyStaffPerformanceSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WeeklyFinanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ['Admin', 'Manager']:
            return Response({"error": "You do not have permission to view this data."}, status=status.HTTP_403_FORBIDDEN)

        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)

        # Fetch customers who checked out during the week
        checked_out_customers = (
            Customer.objects.filter(
                check_out_time__date__range=[start_of_week, end_of_week], checked_out=True
            )
            .annotate(date=TruncDate('check_out_time'))
            .values('date')
            .annotate(total_revenue=Sum('price'))
        )

        revenue_lookup = {
            item['date']: item['total_revenue'] for item in checked_out_customers
        }

        # Build daily stats
        daily_stats = []
        for single_date in (start_of_week + timedelta(days=x) for x in range(7)):  # Iterate for 7 days in the week
            total_revenue = revenue_lookup.get(single_date, 0)
            daily_stats.append({
                'date': single_date,
                'total_revenue': total_revenue,
            })

        data = {
            'week_range': f"{start_of_week} - {end_of_week}",
            'daily_stats': daily_stats,
        }
        serializer = WeeklyFinanceSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
