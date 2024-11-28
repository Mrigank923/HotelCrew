from hoteldetails.models import HotelDetails
from rest_framework import permissions
from rest_framework.generics import CreateAPIView,UpdateAPIView,DestroyAPIView,ListAPIView
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from .models import Task,Announcement
from .serializers import TaskSerializer, AnnouncementSerializer, AnnouncementCreateSerializer, get_shift
from TaskAssignment.permissions import IsAdminorManagerOrReceptionist
from rest_framework.permissions import AllowAny, IsAuthenticated
from authentication.models import Staff, User, DeviceToken, Manager, Receptionist
from authentication.firebase_utils import send_firebase_notification
from django.utils.timezone import now
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from authentication.throttles import *
class ListPagination(PageNumberPagination):
    page_size = 10


class Taskassignment(CreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminorManagerOrReceptionist]
    queryset = Task.objects.all()

    def post(self, request):
         
         if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'User must be authenticated.'
            }, status=status.HTTP_403_FORBIDDEN)
            
   
         
         serializer = self.get_serializer(data=request.data, context={'request': request})
         if serializer.is_valid():
             task = serializer.save()
             user = Staff.objects.get(id=task.assigned_to.id).user
             if not DeviceToken.objects.filter(user=user).exists():
                Staff.objects.filter(id=task.assigned_to.id).update(is_avaliable=False)
             else:
                token = DeviceToken.objects.get(user= user).fcm_token
                send_firebase_notification(fcm_token=token, title=task.title, body=task.description)
                Staff.objects.filter(id=task.assigned_to.id).update(is_avaliable=False)
             return Response({
                    'status': 'success',
                    'message': 'Task created successfully',
                    # 'assigned_by': task.assigned_by,
                    # 'assigned_to': task.assigned_to,
                    'data': serializer.data,
             }, status=status.HTTP_201_CREATED)
         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffTaskListView(ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    pagination_class = ListPagination

    def get_queryset(self):
        user= self.request.user
        user = user.id
        return Task.objects.filter(assigned_to=user).order_by('-created_at')
    

class AllTaskListView(ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminorManagerOrReceptionist]
    queryset = Task.objects.all()
    pagination_class = ListPagination

    def get_queryset(self):
        user= self.request.user
        if user.role == 'Manager':
            user = Manager.objects.get(user=user)
            return Task.objects.filter(hotel=user.hotel).order_by('-created_at')
        elif user.role == 'receptionist':
            user = Receptionist.objects.get(user=user)
            return Task.objects.filter(hotel=user.hotel).order_by('-created_at')
        elif user.role == 'Admin':
            hotel = HotelDetails.objects.get(user = user)
            return Task.objects.filter(hotel=hotel).order_by('-created_at') 
        return Task.objects.none() 

class AllTaskDayListView(APIView):
    permission_classes = [IsAdminorManagerOrReceptionist]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        
        if user.role == 'Manager':
            user = Manager.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'Receptionist':
            user = Receptionist.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'Admin':
            hotel = HotelDetails.objects.get(user=user)
        else:
            return Response({"detail": "Invalid user role"}, status=400)
        
        today = now().date()
        totaltask = Task.objects.filter(hotel=hotel, created_at__date=today).count()
        taskcompleted = Task.objects.filter(hotel=hotel, completed_at__date=today).count()
        taskpending = Task.objects.filter(hotel=hotel, completed_at=None).count()
        
        tasks = Task.objects.filter(hotel=hotel, created_at__date=today).order_by('-created_at')
        serializer = TaskSerializer(tasks, many=True)

        return Response({
            "totaltask": totaltask,
            "taskcompleted": taskcompleted,
            "taskpending": taskpending,
            "tasks": serializer.data
        })
    
class TaskUpdateView(UpdateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminorManagerOrReceptionist]
    throttle_classes = [UpdateTaskUserRateThrottle]
    queryset = Task.objects.all()
    lookup_field = 'pk'


class TaskDeleteView(DestroyAPIView):
    permission_classes = [IsAdminorManagerOrReceptionist]
    queryset = Task.objects.all()
    lookup_field = 'pk'


class TaskStatusUpdateView(APIView):
    permission_classes=[AllowAny]
    throttle_classes = [UpdateTaskUserRateThrottle]
    def patch(self, request, pk=None):
        """
        Allows to update only the status field of a task.
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        # Only allow updating the status field
        status_data = request.data.get("status")
    
        if status_data is not None:
            if status_data == "Completed":
                task.completed_at = timezone.now()
                Staff.objects.filter(id=task.assigned_to.id).update(is_avaliable=True)

                assigned_to = Staff.objects.get(id=task.assigned_to.id)
                devicetoken = DeviceToken.objects.get(user=assigned_to.user)
                send_firebase_notification(fcm_token=devicetoken.fcm_token, title="Task Completed", body="Your task has been completed.")

                assigned_by = task.assigned_by
                devicetoken = DeviceToken.objects.get(user=assigned_by)
                send_firebase_notification(fcm_token=devicetoken.fcm_token, title="Task Completed", body="Task has been completed by staff.")

            task.status = status_data
            task.save()
            return Response({
                "message": "Task status updated successfully",
                "status": task.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Status field is required"}, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementListCreateView(APIView):
    """
    Handles listing all announcements and creating new ones.
    """
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request):
        """
        List all announcements.
        Admin and managers see all announcements, staff see only assigned ones.
        """
        user = request.user
        if user.role == 'Manager':
            user = Manager.objects.get(user=user)
            announcements = Announcement.objects.filter(hotel=user.hotel).order_by('-created_at')
        elif user.role == 'receptionist':
            user = Receptionist.objects.get(user=user)
            announcements = Announcement.objects.filter(hotel=user.hotel).order_by('-created_at')
        elif user.role == 'Admin':
            hotel = HotelDetails.objects.get(user = user)
            announcements = Announcement.objects.filter(hotel=hotel).order_by('-created_at')
        elif user.role == 'Staff':
            staff = Staff.objects.get(user=user)  
            announcements = Announcement.objects.filter(assigned_to=staff).order_by('-created_at')
        else:
            return Response({"detail": "Invalid role."}, status=400)
        
        paginator = PageNumberPagination()
        paginator.page_size = 10 
        paginated_announcements = paginator.paginate_queryset(announcements, request)
        serializer = AnnouncementSerializer(paginated_announcements, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """
        Create a new announcement.
        Only admin and managers can create announcements.
        """
        if not (request.user.role == 'Admin' or request.user.role == 'Manager'):
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AnnouncementCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # serializer.save(assigned_by=request.user)

            # if serializer.data['department'] == 'All':
            #     user = Staff.objects.all()
            # else:
            #     user = Staff.objects.all(department=serializer.data['department'])
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnnouncementDetailView(APIView):
    """
    Handles retrieving and deleting a specific announcement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        """
        Retrieve the announcement object or return a 404 error.
        """
        try:
            return Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Retrieve a specific announcement.
        """
        announcement = self.get_object(pk)
        if announcement is None:
            return Response({"error": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_admin or request.user.is_manager or announcement.assigned_to.filter(id=request.user.staff.id).exists()):
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AnnouncementSerializer(announcement)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete a specific announcement.
        """
        announcement = self.get_object(pk)
        if announcement is None:
            return Response({"error": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.role == 'Admin' or request.user.role == 'Manager'):
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        announcement.delete()
        return Response({"message": "Announcement deleted successfully."}, status=status.HTTP_204_NO_CONTENT)  

class AllAnnouncementDayListView(ListAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminorManagerOrReceptionist]
    queryset = Announcement.objects.all()
    pagination_class = None
    def get_queryset(self):
        user= self.request.user
        if user.role == 'Manager':
            user = Manager.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'receptionist':
            user = Receptionist.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'Admin':
            hotel = HotelDetails.objects.get(user = user)
        
        return Announcement.objects.filter(hotel=hotel,created_at__date=timezone.now().date()).order_by('-created_at')

class AvailableStaffListView(APIView):
    permission_classes = [IsAdminorManagerOrReceptionist]
    
    def get(self, request):
        user= request.user

        if user.role == 'Manager':
            user = Manager.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'receptionist':
            user = Receptionist.objects.get(user=user)
            hotel = user.hotel
        elif user.role == 'Admin':
            hotel = HotelDetails.objects.get(user = user)
        else:
            return Response({"error": "User role not authorized."}, status=403)
        
        shift = get_shift()
        availablestaff = Staff.objects.filter(hotel=hotel,is_avaliable=True,shift=shift).count()
        totalstaff = Staff.objects.filter(hotel=hotel,shift = shift).count()
        staffbusy = totalstaff - availablestaff
       
        return Response({
            "availablestaff": availablestaff,
            "staffbusy": staffbusy,
            "totalstaff": totalstaff
        }, status=200)
