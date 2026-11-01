from django.urls import path
from .views import CookieTokenRefreshView, LogoutView, ProfileUpdateView, RegisterView,LoginAPIView,ProfileApiview, ResetPasswordView, SendOTPView, TokenRefresView, VerifyOTPView
from category.views import CategoryListView,CategoryRetriveApi
from product.views import ProductListView,ProductRetriveApi
from order.views import StripeWebhookAPIView
from userapi.views import Userdata



urlpatterns = [
    #User Authentication Url
    path('register/', RegisterView.as_view(), name='register'),
    path("login/",LoginAPIView.as_view(),name='login'),
    path('refresh/',TokenRefresView.as_view(),name='refresh'),
    path('cookie/refres/',CookieTokenRefreshView.as_view(),name='Cookie-refres'),
    path('logout/',LogoutView.as_view(),name='logout'),



    #forget password
    path("send-otp/",SendOTPView.as_view(),name='send-otp'),
    path('verify-otp/',VerifyOTPView.as_view(),name='verify-otp'),
    path('reset-password/',ResetPasswordView.as_view(),name='reset-password'),
    

    


    #profileUrl
    path("profile/",ProfileApiview.as_view(),name='profile'),
    path("profile/update/",ProfileUpdateView.as_view(),name="profile-update",),
    path("userdata/",Userdata.as_view(),name="user-data"),


    #category
    path("category/",CategoryListView.as_view(),name='category-list'),
    path("category/<int:pk>/",CategoryRetriveApi.as_view(),name='category-retrive'),


    #product
    path("product/",ProductListView.as_view(),name='product-list'),
    path("product/<int:pk>/",ProductRetriveApi.as_view(),name='product-retrive'),


    #web hook stripe
    path("webhook/", StripeWebhookAPIView.as_view(),name="stripe-webhook"),
    
]