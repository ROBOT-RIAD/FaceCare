from django.urls import path
from .views import RegisterView,LoginAPIView,ProfileApiview


urlpatterns = [
    #User Authentication Url
    path('register/', RegisterView.as_view(), name='register'),
    path("login/",LoginAPIView.as_view(),name='login'),

    


    #profileUrl
    path("profile/",ProfileApiview.as_view(),name='profile'),
    
]