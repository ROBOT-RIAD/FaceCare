from django.db import models
from account.models import User

# Create your models here.
ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]


class Chat(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="chats")
    title = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Chat {self.id}"



class Message(models.Model):
    chat = models.ForeignKey(Chat,on_delete=models.CASCADE,related_name="messages")
    role = models.CharField(max_length=20,choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.role} - {self.chat_id}"
