from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated ,AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from backend.throttle import RegisterThrottle
from rest_framework.response import Response

from backend.response import success_response


from .models import Profile,User
from .serializers import RegisterSerializer,AuthResponseSerializer,LoginSerializer,ProfileSerializer, ResetPasswordSerializer, SendOTPSerializer, VerifyOTPSerializer,ProfileUpdateSerializer

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




class TokenRefresView(TokenRefreshView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Refresh token JWT Bearer",
        operation_description="Refresh JWT access token using a valid refresh token.",
        tags=["Authentication"],
    )
    def post (self , request , *args, **kwargs):
        response = super().post(request , *args, **kwargs)
        return success_response(message="New Token get successfully",data=response.data,status_code=status.HTTP_200_OK)




class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Logout authenticated user",
        operation_description=(
            "Logout the authenticated user by deleting the "
            "access token and refresh token stored in HttpOnly cookies."
        ),
        tags=["Authentication"],
        responses={
            200: openapi.Response(
                description="Logout successful."
            ),
            401: openapi.Response(
                description="Authentication credentials were not provided or are invalid."
            ),
        },
    )
    def post(self, request):

        response = success_response(
            message="Logout successful.",
            data={},
            status_code=status.HTTP_200_OK
        )

        response.delete_cookie(
            settings.JWT_ACCESS_COOKIE_NAME
        )

        response.delete_cookie(
            settings.JWT_REFRESH_COOKIE_NAME
        )

        return response




class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Refresh JWT Token HttpOnly cookie",
        operation_description=(
            "Generate a new access token using the refresh token "
            "stored in the HttpOnly cookie."
        ),
        tags=["Authentication"],
        responses={
            200: "Token refreshed successfully.",
            401: "Invalid or expired refresh token.",
        },
    )
    def post(self, request, *args, **kwargs):

        refresh_token = request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE_NAME
        )

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "error": {
                        "type": "NotAuthenticated",
                        "message": "Refresh token not found.",
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(
            data={
                "refresh": refresh_token
            }
        )

        try:
            serializer.is_valid(
                raise_exception=True
            )

        except InvalidToken:
            return Response(
                {
                    "success": False,
                    "error": {
                        "type": "InvalidToken",
                        "message": "Invalid or expired refresh token.",
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


        access_token = serializer.validated_data["access"]

        new_refresh_token = serializer.validated_data.get(
            "refresh"
        )

        response = success_response(
            message="Token refreshed successfully.",
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
            },
            status_code=status.HTTP_200_OK,
        )


        response.set_cookie(
            key=settings.JWT_ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=settings.JWT_ACCESS_COOKIE_MAX_AGE,
            httponly=settings.JWT_COOKIE_HTTP_ONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )


        if new_refresh_token:

            response.set_cookie(
                key=settings.JWT_REFRESH_COOKIE_NAME,
                value=new_refresh_token,
                max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
                httponly=settings.JWT_COOKIE_HTTP_ONLY,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE,
            )

        return response

 


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    @swagger_auto_schema(
        operation_summary="Send password reset OTP",
        operation_description=(
            "Generate a 6-digit OTP and send it "
            "to the user's email. "
            "The OTP is valid for 5 minutes."
        ),
        request_body=SendOTPSerializer,
        tags=["Forget Password"],
        responses={
            200: "OTP sent successfully.",
            400: "Invalid email.",
        },
    )
    def post(self,request,*args,**kwargs):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(
            message="OTP sent successfully.OTP is valid for 5 minutes.",
            status_code=status.HTTP_200_OK
        )




class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Verify password reset OTP",

        operation_description=(
            "Verify the OTP sent to the user's email."
        ),

        request_body=VerifyOTPSerializer,

        tags=["Forget Password"],

        responses={
            200: "OTP verified successfully.",
            400: "Invalid or expired OTP.",
        },
    )
    def post(self,request,*args,**kwargs):

        serializer = VerifyOTPSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )
        return success_response(
            message="OTP verified successfully.",
            data=serializer.validated_data["reset_token"],
            status_code=status.HTTP_200_OK
        )

  


class ResetPasswordView(APIView):

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]


    @swagger_auto_schema(
        operation_summary="Reset password",

        operation_description=(
            "Reset the user's password."
        ),

        request_body=ResetPasswordSerializer,

        tags=["Forget Password"],

        responses={
            200: "Password reset successfully.",
            400: "Invalid password data.",
        },
    )
    def post(self,request,*args,**kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Password reset successfully.",
            status_code=status.HTTP_200_OK
        )

  



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




class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    @swagger_auto_schema(
        operation_summary="Update User Profile",
        operation_description="Update the profile of the authenticated user.",
        tags=["Profile"],
        request_body=ProfileUpdateSerializer,
        responses={200: openapi.Response('User Profile', ProfileSerializer)}
    )
    def patch(self, request, *args, **kwargs):
        profile = Profile.objects.select_related("user").get(user=request.user)
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = ProfileSerializer(profile)
        return success_response(
            message="Profile updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )


