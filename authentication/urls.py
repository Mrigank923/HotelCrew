from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    path('registrationOTP/', RegistrationOTPView.as_view(), name='register_otp'),
    path('register/', RegisterWithOTPView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgetpassword/', ForgetPassword.as_view(), name='forgetpassword'),
    path('resetpassword/', ResetPassView.as_view(), name='resetpassword'),
]