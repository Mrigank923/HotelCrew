from itertools import chain
from collections import Counter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from authentication.throttles import *
import pandas as pd
from attendance.permissions import *
from authentication.models import User,Manager,Receptionist,Staff
from hoteldetails.models import HotelDetails
from hoteldetails.utils import get_hotel
from django.core import serializers
from hoteldetails.serializers import HotelSerializer
from django.db import transaction
from .serializers import StaffListSerializer,UserSerializer,HotelUpdateSerializer,ProfileUpdateSerializer,ScheduleListSerializer,ProfileViewSerializer
import re
from rest_framework.pagination import PageNumberPagination

class ListPagination(PageNumberPagination):
    page_size = 10

class StaffListView(ListAPIView):
     permission_classes = [IsManagerOrAdmin]

     def get(self, request):
        user = request.user
        try:
            user_hotel= get_hotel(user)
            if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        except HotelDetails.DoesNotExist:
            return Response(
                {'message': 'No hotel is associated with you!.'},
                status=status.HTTP_200_OK
            )
        
        managers=Manager.objects.filter(hotel=user_hotel)
        staffs=Staff.objects.filter(hotel=user_hotel)
        receptionists=Receptionist.objects.filter(hotel=user_hotel)
        
        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))
        
        department_count = Counter(staff.department for staff in staffs)
        total_departments = len(department_count)
        staff_per_department = dict(department_count)
        
        serializer = StaffListSerializer(non_admin_users, many=True)
        return Response({'status': 'success','total_departments': total_departments,'staff_per_department': staff_per_department,'staff_list': serializer.data}, status=200)
    
class TotalDepartmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            user_hotel= get_hotel(user)
            if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        except HotelDetails.DoesNotExist:
            return Response(
                {'message': 'No hotel is associated with you!.'},
                status=status.HTTP_200_OK
            )
        
        staffs=Staff.objects.filter(hotel=user_hotel)
        department_count = Counter(staff.department for staff in staffs)
        total_departments = len(department_count)
        staff_per_department = dict(department_count)
        
        return Response({'status': 'success','total_departments': total_departments,'staff_per_department': staff_per_department}, status=200)

class CreateCrewView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'status': 'error', 'message': 'User must be authenticated.'}, status=status.HTTP_403_FORBIDDEN)
        
        
        user = request.user
        try:
            user_hotel = get_hotel(user)
            if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        except HotelDetails.DoesNotExist:
            return Response({'status': 'error', 'message': 'No hotel is associated with the authenticated user.'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        role = data.get('role', 'Staff').capitalize()
        email= data.get('email')
        user_name =data.get('user_name').strip()
        department = data.get('department', 'Housekeeping').capitalize()
        salary = data.get('salary', 0)
        upi_id = data.get('upi_id')
        shift = data.get('shift', 'Morning').capitalize()
        

        if not email:
            return Response({'status': 'error', 'message': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.search(r'[a-zA-Z0-9]', user_name):
            return Response({'status':'error','message':"Username must contain at least one letter or number and cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
       
        valid_roles = dict(User.ROLE_CHOICES).keys()
        if role not in valid_roles:
            return Response({'status': 'error', 'message':'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)


        try:
            user = User.objects.create_user(email=email, user_name=user_name, role=role, upi_id=upi_id, salary=salary)
            
            if role == 'Manager':
                Manager.objects.create(user=user, hotel=user_hotel,shift=shift)
            elif role == 'Receptionist':
                Receptionist.objects.create(user=user, hotel=user_hotel,shift=shift)
            else:
                Staff.objects.create(user=user, hotel=user_hotel, department=department,shift=shift)

        except Exception as e:
            return Response({'status': 'error', 'message': f"Error creating user: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response({'status': 'success', 'message': 'User created successfully.', 'user': serializer.data}, status=status.HTTP_201_CREATED)

class UpdateCrewView(APIView):
    permission_classes = [IsManagerOrAdminOrSelf]
        
    def get(self, request, user_id):
        if not request.user.is_authenticated:
            return Response({'status': 'error', 'message': 'User must be authenticated.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response({'status': 'success', 'user': serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        if not request.user.is_authenticated:
            return Response({'status': 'error', 'message': 'User must be authenticated.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.role == 'Admin' :
            return Response({'status': 'error', 'message': 'You cannot update an Admin.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user_hotel = get_hotel(user)
        except HotelDetails.DoesNotExist:
            return Response({'status': 'error', 'message': 'No hotel is associated with the authenticated user.'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        new_role = data.get('role', user.role).capitalize()
        new_email = data.get('email', user.email)
        user_name = data.get('user_name', user.user_name)
        department = data.get('department')
        salary = data.get('salary', user.salary)
        upi_id = data.get('upi_id', user.upi_id)
        shift = data.get('shift')

        if new_email != user.email:
            try:
                validate_email(new_email)
            except ValidationError:
                return Response({'status': 'error', 'message': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=new_email).exists():
                return Response({'status': 'error', 'message': 'This email is already in use.'}, status=status.HTTP_400_BAD_REQUEST)

            user.email = new_email


        valid_roles = dict(User.ROLE_CHOICES).keys()
        if new_role not in valid_roles:
            return Response({'status': 'error', 'message': f'Invalid role. Choose from {", ".join(valid_roles)}.'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():

            if new_role != user.role:

                if user.role == 'Manager':
                    Manager.objects.filter(user=user).delete()
                elif user.role == 'Receptionist':
                    Receptionist.objects.filter(user=user).delete()
                elif user.role == 'Staff':
                    Staff.objects.filter(user=user).delete()

                if new_role == 'Manager':
                    Manager.objects.create(user=user, hotel=user_hotel,shift=shift)
                elif new_role == 'Receptionist':
                    Receptionist.objects.create(user=user, hotel=user_hotel,shift=shift)
                elif new_role == 'Staff':
                    Staff.objects.create(user=user, hotel=user_hotel, department=department,shift=shift)

        user.user_name = user_name
        user.salary = salary
        user.upi_id = upi_id
        user.role = new_role

        try:
            user.save()
        except Exception as e:
            return Response({'status': 'error', 'message': f"Error updating user: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response({'status': 'success', 'message': 'User updated successfully.', 'user': serializer.data}, status=status.HTTP_200_OK)

class DeleteCrewView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def delete(self, request, user_id):
        if not request.user.is_authenticated:
            return Response({
                'status': 'error',
                'message': 'You are not allowed to do this operation.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user_to_delete = User.objects.get(id=user_id)
            if user_to_delete.role == 'Admin':
                return Response({
                    'status': 'error',
                    'message': 'You cannot delete an Admin.'
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    
        hotel = get_hotel(request.user)
        if not hotel:
            return Response({
                'status': 'error',
                'message': 'No hotel is associated with the authenticated user.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_to_delete_hotel = get_hotel(user_to_delete)
        if not user_to_delete_hotel:
            return Response({
                'status': 'error',
                'message': 'No hotel is associated with the user to be deleted.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user_to_delete_hotel == hotel:
            user_to_delete.delete()

        # if user_to_delete.role == 'Manager':
        #     Manager.objects.filter(user=user_to_delete,hotel=hotel).delete()
        # elif user_to_delete.role == 'Receptionist':
        #     Receptionist.objects.filter(user=user_to_delete,hotel=hotel).delete()
        # elif user_to_delete.role == 'Staff':
        #     Staff.objects.filter(user=user_to_delete,hotel=hotel).delete()
        # else:
        #     return Response({
        #         'status': 'error',
        #         'message': 'User role not recognized.'
        #     }, status=status.HTTP_400_BAD_REQUEST)

      
        else:
            return Response({
                'status': 'error',
                'message': 'User does not belong to this hotel.'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': 'User and associated data deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)
        
class GetHotelDetailsView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        try:
            hotel_details = get_hotel(request.user)
            if not hotel_details:
                raise serializers.ValidationError("Hotel information is required.")
        except HotelDetails.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No hotel is associated with the authenticated user.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotelUpdateSerializer(hotel_details)
        return Response({
            'status': 'success',
            'message': 'Hotel details retrieved successfully.',
            'hotel_details': serializer.data
        }, status=status.HTTP_200_OK)

class UpdateHotelDetailsView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request):
        try:
            hotel_details = HotelDetails.objects.get(user=request.user)
        except HotelDetails.DoesNotExist:
                serializer = HotelSerializer(data=request.data,context={'request':request})
                if serializer.is_valid():
                    hotel= serializer.save()

                    return Response({
                        'status': 'success',
                        'message': 'Hotel registered successfully',
                        'hotel': serializer.data,
                    }, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotelUpdateSerializer(hotel_details, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Hotel details updated successfully.',
                'hotel': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UpdateProfileUserRateThrottle]
    
    def get(self, request):
        user = request.user
        serializer = ProfileViewSerializer(user)
        return Response({'status': 'success', 'user': serializer.data}, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save() 
            return Response({'status':'success','message':'Profile updated successfully.','user':serializer.data}, status=status.HTTP_200_OK)

        return Response({'status':'error','message':'Profile update failed.','errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class ScheduleListView(ListAPIView):
     permission_classes = [IsManagerOrAdmin]

     def get(self, request):
        
        try:
           user_hotel = get_hotel(request.user)
           if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        
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
        
        # department_count = Counter(staff.department for staff in staffs)
        # total_departments = len(department_count)
        # staff_per_department = dict(department_count)
        
        serializer = ScheduleListSerializer(non_admin_users, many=True)
        return Response({'status': 'success','schedule_list': serializer.data}, status=200)
    
class ChangeShiftView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def put(self, request, user_id):
        shift = request.data.get('shift')

        if not shift:
            return Response(
                {"error": "shift is required in the request body."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if shift not in ['Morning', 'Evening', 'Night']:
            return Response(
                {"error": "Invalid shift. Choose from Morning, Evening, Night."},
                status=status.HTTP_400_BAD_REQUEST)

        try:
           user_hotel = get_hotel(request.user)
           if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        
        except HotelDetails.DoesNotExist:
            return Response(
                {"error": "You are not associated with a hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_instance = None

        if Staff.objects.filter(user_id=user_id, hotel=user_hotel).exists():
            user_instance = Staff.objects.get(user_id=user_id, hotel=user_hotel)

        elif Manager.objects.filter(user_id=user_id, hotel=user_hotel).exists():
            user_instance = Manager.objects.get(user_id=user_id, hotel=user_hotel)

        elif Receptionist.objects.filter(user_id=user_id, hotel=user_hotel).exists():
            user_instance = Receptionist.objects.get(user_id=user_id, hotel=user_hotel)

        if not user_instance:
            return Response(
                {"error": "User does not belong to this hotel or does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        user_instance.shift = shift
        user_instance.save()

        return Response(
            {"message": "Shift updated successfully.", "user_id": user_id, "new_shift": shift},
            status=status.HTTP_200_OK
        )
        
class MassCreateStaffView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'status': 'error', 'message': 'User must be authenticated.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the hotel associated with the authenticated user
           hotel = get_hotel(request.user)
           if not hotel:
                raise serializers.ValidationError("Hotel information is required.")
        
        except HotelDetails.DoesNotExist:
            return Response({'status': 'error', 'message': 'No hotel is associated with the authenticated user.'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES.get('staff_excel_sheet')

        if not excel_file:
            return Response({'status': 'error', 'message': 'Excel file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(excel_file)

            # Iterate over the rows in the DataFrame
            created_users = []
            for _, row in df.iterrows():
                role = row.get('Role', 'Staff').capitalize()  # Default to 'Staff' if role is not specified
                email = row.get('Email')
                user_name = row.get('Name')
                department = row.get('department', 'Housekeeping')
                salary = row.get('salary', 0)
                shift = row.get('shift', 'Morning')
                upi_id = row.get('upi_id')

                # Validate email presence
                if not email:
                    return Response({'status': 'error', 'message': 'Email is required in every row.'}, status=status.HTTP_400_BAD_REQUEST)
                
                valid_roles = dict(User.ROLE_CHOICES).keys()
                if role not in valid_roles:
                    return Response({'status': 'error', 'message': f'Invalid role in the row: {role}'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Create the User instance
                    user = User.objects.create_user(email=email, user_name=user_name, role=role, upi_id=upi_id, salary=salary)
                    
                    # Based on the role, create the respective model instance
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

                    created_users.append(user)
                    
                except Exception as e:
                    return Response({'status': 'error', 'message': f"Error processing row: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Serialize the created users
            serializer = UserSerializer(created_users, many=True)
            return Response({'status': 'success', 'message': 'Staff members created successfully.', 'data': serializer.data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'status': 'error', 'message': f"Error processing Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class DeleteStaffByDepartmentView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def delete(self, request):
        user = request.user
        department = request.data.get('department', '').capitalize()

        if not department:
            return Response(
                {'status': 'error', 'message': 'Department is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_hotel = get_hotel(user)
            if not user_hotel:
                return Response(
                    {'status': 'error', 'message': 'User is not associated with any hotel.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Error retrieving hotel: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        with transaction.atomic():
            staff_to_delete = Staff.objects.filter(hotel=user_hotel, department=department)
            user_ids_to_delete = staff_to_delete.values_list('user_id', flat=True)

            deleted_users_count, _ = User.objects.filter(id__in=user_ids_to_delete).delete()

        return Response(
            {
                'status': 'success',
                'message': f'All staff from the {department} department were deleted successfully.',
            },
            status=status.HTTP_200_OK
        )

class StaffPaginationListView(ListAPIView):
     permission_classes = [IsManagerOrAdmin]
     pagination_class = ListPagination
     def get(self, request):
        user = request.user
        try:
            user_hotel= get_hotel(user)
            if not user_hotel:
                raise serializers.ValidationError("Hotel information is required.")
        except HotelDetails.DoesNotExist:
            return Response(
                {'message': 'No hotel is associated with you!.'},
                status=status.HTTP_200_OK
            )
        
        managers=Manager.objects.filter(hotel=user_hotel)
        staffs=Staff.objects.filter(hotel=user_hotel)
        receptionists=Receptionist.objects.filter(hotel=user_hotel)
        
        non_admin_users = list(chain(
            (manager.user for manager in managers),
            (staff.user for staff in staffs),
            (receptionist.user for receptionist in receptionists)
        ))
        paginated_users = self.paginate_queryset(non_admin_users)
        serializer = StaffListSerializer(paginated_users, many=True)
        return self.get_paginated_response({'status': 'success', 'staff_list': serializer.data})