
from django.core.mail import send_mail
from django.conf import settings
from HotelCrew.settings import EMAIL_HOST_USER
from django.utils.html import format_html
                

    
def otp_for_reset(email, otp):
    subject = "Your OTP to Reset Password"
    message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #ffffff; padding: 20px;">
            <table align="center" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 20px;">
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <h2 style="color: #5D69F8; margin-bottom: 10px;">Password Reset Request</h2>
                        <p style="color: #5663AC; font-size: 16px; margin: 0;">
                            You requested to reset your password. Use the OTP below to complete the process.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 30px;">
                        <div style="display: inline-block; background-color: #5D69F8; color: #ffffff; font-size: 24px; font-weight: bold; padding: 10px 20px; border-radius: 5px;">
                            {otp}
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <p style="color: #5663AC; font-size: 14px; margin: 0;">
                            This OTP is valid for a limited time. Please do not share it with anyone.
                        </p>
                        <p style="color: #5663AC; font-size: 14px; margin-top: 10px;">
                            If you didn’t request a password reset, you can ignore this message.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <p style="color: #333; font-size: 16px; font-weight: bold; margin: 0;">
                            Thank you,<br>HotelCrew Team
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    return send_mail(subject, "", from_email, recipient_list, html_message=message)

def otp_for_register(user_name, email, otp):
    subject = "Your OTP for Registration"
    message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #ffffff; padding: 20px;">
            <table align="center" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 20px;">
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <h2 style="color: #5D69F8; margin-bottom: 10px;">Welcome to HotelCrew!</h2>
                        <p style="color: #5663AC; font-size: 16px; margin: 0;">
                            To complete your registration, please enter the OTP below.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 30px;">
                        <div style="display: inline-block; background-color: #5D69F8; color: #ffffff; font-size: 24px; font-weight: bold; padding: 10px 20px; border-radius: 5px;">
                            {otp}
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <p style="color: #5663AC; font-size: 14px; margin: 0;">
                            This OTP is valid for a limited time. Please do not share it with anyone.
                        </p>
                        <p style="color: #5663AC; font-size: 14px; margin-top: 10px;">
                            If you did not initiate this registration, please ignore this email.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <p style="color: #333; font-size: 16px; font-weight: bold; margin: 0;">
                            Thank you for joining us,<br>HotelCrew Team
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    return send_mail(subject, "", from_email, recipient_list, html_message=message)


def send_registration_email(email, password, role, user_name):
    subject = "Registration Successful"
    message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #ffffff; padding: 20px;">
            <table align="center" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 20px;">
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <h2 style="color: #5D69F8; margin-bottom: 10px;">Registration Successful!</h2>
                        <p style="color: #5663AC; font-size: 16px; margin: 0;">
                            Dear {user_name},
                        </p>
                        <p style="color: #5663AC; font-size: 16px; margin-top: 10px;">
                            Your account as a {role} has been successfully created.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px;">
                        <p style="color: #333; font-size: 14px; margin: 0;">
                            Your login credentials are:
                        </p>
                        <ul style="color: #333; font-size: 14px; margin: 10px 0 0 20px; padding: 0;">
                            <li><strong>Email:</strong> {email}</li>
                            <li><strong>Password:</strong> {password}</li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center; padding: 20px;">
                        <p style="color: #333; font-size: 16px; font-weight: bold; margin: 0;">
                            Regards,<br>HotelCrew Team
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    return send_mail(subject, "", from_email, recipient_list, html_message=message)