from celery import shared_task
from .utils import otp_for_reset, otp_for_register, send_registration_email

@shared_task
def send_otp_for_reset_task(email, otp):
    # Wrapper for the otp_for_reset function
    otp_for_reset(email, otp)

@shared_task
def send_otp_for_register_task(user_name, email, otp):
    # Wrapper for the otp_for_register function
    otp_for_register(user_name, email, otp)

@shared_task
def send_registration_email_task(email, password, role, user_name):
    # Wrapper for the send_registration_email function
    send_registration_email(email, password, role, user_name)
