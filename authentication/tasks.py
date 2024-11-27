from celery import shared_task
from django.utils.timezone import now
from .models import DeviceToken
from TaskAssignment.models import Task
from .firebase_utils import send_firebase_notification

@shared_task
def notify_overdue_tasks():

    overdue_tasks = Task.objects.filter(deadline__lt=now(), status='pending')
    
    for task in overdue_tasks:
        # Notify the staff assigned
        try:
            staff_token = DeviceToken.objects.get(user=task.assigned_to).fcm_token
            send_firebase_notification(
                fcm_token=staff_token,
                title="Overdue Task Alert",
                body=f"The task '{task.title}' is overdue. Please update the status."
            )
        except DeviceToken.DoesNotExist:
            print(f"FCM token not found for staff: {task.assigned_to.email}")
        
        # Notify the manager who assigned
        try:
            manager_token = DeviceToken.objects.get(user=task.assigned_by).fcm_token
            send_firebase_notification(
                fcm_token=manager_token,
                title="Task Overdue Alert",
                body=f"The task '{task.title}', assigned to {task.assigned_to.user_name}, is overdue."
            )
        except DeviceToken.DoesNotExist:
            print(f"FCM token not found for manager: {task.assigned_by.email}")
