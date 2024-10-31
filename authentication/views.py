from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import *
from django.http import JsonResponse
from rest_framework.generics import *

# this is just a placeholder view for the deault path
def home_view(request):
    return JsonResponse({"message": "Welcome to the HotelCrew!"})


# views.py

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        password = request.data.get('password')

        if not all([phone_number, email, first_name, last_name, password]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
   
            otp_sent = send_phone_otp(phone_number)
            PhoneOTP.objects.update_or_create(
                phone_number=phone_number,
                defaults={
                    'otp': otp_sent,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': password,
                }
            )
            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
class VerifyPhoneOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp = request.data.get('otp')

        try:
            otp_instance = PhoneOTP.objects.get(phone_number=phone_number)
            print(otp_instance.otp)
        except PhoneOTP.DoesNotExist:
            return Response({"error": "Phone number not found."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_instance.otp != int(otp):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(
                email=otp_instance.email,
                first_name=otp_instance.first_name,
                last_name=otp_instance.last_name,
                phone_number=otp_instance.phone_number,
                password=otp_instance.password
            )

            otp_instance.delete()
            return Response({
                'status': 'success',
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 'success',
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }
                })
            return Response({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ForgetPassword(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = ForgetPassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message' : ['OTP sent on email']}, status=status.HTTP_200_OK)
    
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message' : ['OTP Verified']}, status=status.HTTP_200_OK)

class ResetPassView(UpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPassSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'messsage':['Password changed successfully']}, status=status.HTTP_200_OK)