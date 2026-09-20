from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from backend.services import delete_image_from_cloudinary


@shared_task(queue="email")
def send_otp_email(user_id, otp):

    try:
        user = User.objects.get(id=user_id)

        send_mail(
            subject="Your OTP Code",
            message=(
                f"Hello {user.username},\n\n"
                f"Your OTP code is: {otp}\n\n"
                f"This OTP is valid for 5 minutes."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"OTP sent to {user.email}"

    except User.DoesNotExist:
        return "User not found"




@shared_task(queue="image")
def delete_cloudinary_image(public_id):
    try:
        if not public_id:
            return "Public ID not provided."

        deleted = delete_image_from_cloudinary(public_id)

        if deleted:
            return f"Image deleted successfully: {public_id}"

        return f"Image deletion failed: {public_id}"

    except Exception as e:
        return f"Image deletion failed: {str(e)}"