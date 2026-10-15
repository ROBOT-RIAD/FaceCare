from django.db import models
from account.models import User

# Create your models here.

class Notification(models.Model):
    sender_user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="sent_notifications",)
    receiver_user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="received_notifications",)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.JSONField(blank=True, null=True)
    read = models.BooleanField(default=False)
    admin_notification = models.BooleanField(default=False)
    user_notification = models.BooleanField(default=False)
    all_user_notification = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        receiver = (
            self.receiver_user.username
            if self.receiver_user
            else "All users / No receiver"
        )
        return f"Notification for {receiver}: {self.title}"




    
