from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import ROLE_CHOICES,GENDER

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20,choices=ROLE_CHOICES,default="user")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']



class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    full_name = models.CharField(max_length=200,blank=True,null=True)
    gender = models.CharField(max_length=50,choices=GENDER,blank=True,null=True)
    contact_number = models.CharField(max_length=20,null=True, blank=True)
    skin_type = models.CharField(max_length=50,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    image = models.URLField(max_length=1000,blank=True,null=True)
    cloudinary_public_id = models.CharField(max_length=500,unique=True,blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
