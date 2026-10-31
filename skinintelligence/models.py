from django.db import models
from account.models import User

# Create your models here.

class SkinIntelligence(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="skin_intelligence")

    skin_type = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    skin_concerns = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.skin_type} - {self.user}"





class Routine(models.Model):
    skin_intelligence = models.OneToOneField(SkinIntelligence,on_delete=models.CASCADE,related_name="routine")
    routine_json = models.JSONField(default=dict, blank=True)
    is_saved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Routine - {self.skin_intelligence.user}"
