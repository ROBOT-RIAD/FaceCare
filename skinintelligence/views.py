from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from .serializers import CreateSkinIntelligenceRoutineSerializer,RoutineResponseSerializer
from account.permissions import IsUserRole


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class RutineCreateApiview(APIView):
    permission_classes = [IsUserRole]
    parser_classes = [MultiPartParser, FormParser]
    @swagger_auto_schema(
        operation_summary="Generate AI Skincare Routine",
        operation_description=(
            "Generate a personalized morning and night skincare "
            "routine using user skin information, face image, "
            "available products and Groq LLM."
        ),
        consumes=["multipart/form-data"],
        request_body=CreateSkinIntelligenceRoutineSerializer,
        responses={
            201: RoutineResponseSerializer,
            400: "Validation error",
            401: "Unauthorized",
            403: "Permission denied",
            500: "Internal server error",
        },
        tags=["Skin-Intelligence"]
    )
    def post(self, request):
        serializer = CreateSkinIntelligenceRoutineSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()
        response_data = RoutineResponseSerializer(routine).data
        return success_response(
            message="Skincare routine generated successfully",
            data=response_data,
            status_code=status.HTTP_201_CREATED
        )