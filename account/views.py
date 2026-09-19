from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from backend.throttle import RegisterThrottle

from backend.response import success_response


from .models import Profile,User
from .serializers import RegisterSerializer,AuthResponseSerializer,LoginSerializer,ProfileSerializer

#jwt
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken


#swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class RegisterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    # throttle_classes = [RegisterThrottle]
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Register a new user and return JWT tokens",
        request_body=RegisterSerializer,
        tags=["Authentication"],
        responses={200: AuthResponseSerializer}          
    )

    def post(self,request,*args,**kwargs):
        serializer = RegisterSerializer(data=request.data,context={"request":request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh['id'] = user.id
        refresh['role'] = user.role
        access_token = refresh.access_token

        auth_data = {
            "access_token": str(access_token),
            "refresh_token": str(refresh),
        }
        response_serializer = AuthResponseSerializer(auth_data)

        response = success_response(
            message="Registration successful.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

        response.set_cookie(
            key=settings.JWT_ACCESS_COOKIE_NAME,
            value=str(access_token),
            max_age=settings.JWT_ACCESS_COOKIE_MAX_AGE,
            httponly=settings.JWT_COOKIE_HTTP_ONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )

        response.set_cookie(
            key=settings.JWT_REFRESH_COOKIE_NAME,
            value=str(refresh),
            max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
            httponly=settings.JWT_COOKIE_HTTP_ONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )
        return response



class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Login API",
        operation_description="Login with email and password and return JWT tokens.",
        request_body=LoginSerializer,
        tags=["Authentication"],
        responses={200: AuthResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        access_token = data["access"]
        refresh_token = data["refresh"]
        auth_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        response_serializer = AuthResponseSerializer(auth_data)
        response = success_response(
            message="Login successful.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )

        response.set_cookie(
            key=settings.JWT_ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=settings.JWT_ACCESS_COOKIE_MAX_AGE,
            httponly=settings.JWT_COOKIE_HTTP_ONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )

        response.set_cookie(
            key=settings.JWT_REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
            httponly=settings.JWT_COOKIE_HTTP_ONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )

        return response




class ProfileApiview(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get User Profile",
        operation_description="Retrieve the profile of the authenticated user.",
        tags=["Profile"],
        responses={200: openapi.Response('User Profile', ProfileSerializer)}
    )
    def get(self, request, *args, **kwargs):
        profile = Profile.objects.select_related("user").get(user=request.user)
        serializer = ProfileSerializer(profile)
        return success_response(
            message="Profile retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )




