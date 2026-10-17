from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_realtime_notification(notification):
    channel_layer = get_channel_layer()

    if channel_layer is None:
        return

    payload = {
        "type": "send_notification",
        "data": {
            "id": notification.id,
            "title": notification.title,
            "body": notification.body,
            "data": notification.data or {},
            "read": notification.read,
            "created_at": notification.created_at.isoformat(),
        },
    }

    # 1. Send to all connected admins
    if notification.admin_notification:
        async_to_sync(channel_layer.group_send)(
            "admin_notifications",
            payload,
        )

    # 2. Send to the specific receiver
    if notification.user_notification and notification.receiver_user_id:
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.receiver_user_id}",
            payload,
        )

    # 3. Send to all connected users
    if notification.all_user_notification:
        async_to_sync(channel_layer.group_send)(
            "all_users_notifications",
            payload,
        )
