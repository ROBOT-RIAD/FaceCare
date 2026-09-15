from django.urls import path
from .views import RegisterView


urlpatterns = [
    #User Authentication Url
    path('register/', RegisterView.as_view(), name='register'),
    
]