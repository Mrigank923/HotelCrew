
from django.core.mail import send_mail
from django.conf import settings
from HotelCrew.settings import EMAIL_HOST_USER
import random,requests
from .models import PhoneOTP
                

    
def otp_for_reset(email,otp):
     subject="OTP to Reset Password "
     message = f"""
Your OTP to reset your password is:
{otp}
Do not share your otp with anyone.
-team hotelcrew
""" 
     
     from_email = settings.EMAIL_HOST_USER
     recipient_list = [email]

     return send_mail(subject, message, from_email , recipient_list)


def send_phone_otp(phone_number):
    otp = random.randint(1000, 9999)
    otp_instance, created = PhoneOTP.objects.update_or_create(
        phone_number=phone_number,
        defaults={'otp': otp}  
    )
    
    print(f"Generated OTP: {otp_instance.otp} for {phone_number}")
  
    url = f'https://2factor.in/API/V1/{settings.API_KEY}/SMS/{phone_number}/{otp}'
    response = requests.get(url)
    data = response.json()

    if data['Status'] == 'Success':
        return otp_instance.otp
    else:
        raise Exception('Failed to send OTP')
 

