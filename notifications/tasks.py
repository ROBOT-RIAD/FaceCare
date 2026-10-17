from celery import shared_task
from django.db import transaction
from notifications.models import Notification
from account.models import User
from .utils import send_realtime_notification


@shared_task(queue="notifications")
def create_notification_task(title, body,data , sender_user=None, receiver_user=None, admin_notification=False, user_notification=False, all_user_notification=False):
    
    notification = Notification.objects.create(
        title=title,
        body=body,
        data=data,
        sender_user=sender_user,
        receiver_user=receiver_user,
        admin_notification=admin_notification,
        user_notification=user_notification,
        all_user_notification=all_user_notification,
    )

    transaction.on_commit(
        lambda: send_realtime_notification(notification)
    )
    return notification.id