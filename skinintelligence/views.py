from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from .serializers import CreateSkinIntelligenceRoutineSerializer,RoutineResponseSerializer,RutineUpdateSrializer
from account.permissions import IsUserRole
from .models import Routine
from django.shortcuts import get_object_or_404


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




class UserGetHerSaveRutineAPIView(APIView):
    permission_classes = [IsUserRole]
    @swagger_auto_schema(
        operation_summary="Get All Saved Routines",
        operation_description=(
            "Retrieve all saved routines belonging to the authenticated user."
        ),
        responses={
            200: RoutineResponseSerializer(many=True),
            401: "Unauthorized",
            403: "Permission denied",
            500: "Internal server error",
        },
        tags=["Skin-Intelligence"]
    )
    def get(self, request):
        routines = Routine.objects.filter(
            skin_intelligence__user=request.user,
            is_saved=True
        ).select_related("skin_intelligence").order_by("-created_at")

        serializer = RoutineResponseSerializer(
            routines,
            many=True
        )

        return success_response(
            message="Saved routines retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )




class RitriveAndUpdateRutine(APIView):
    permission_classes = [IsUserRole]

    def get_object(self, request, pk):
        return get_object_or_404(
            Routine,
            pk=pk,
            skin_intelligence__user=request.user
        )

    @swagger_auto_schema(
        operation_summary="Retrieve Routine",
        operation_description="Retrieve a specific routine belonging to the authenticated user.",
        responses={
            200: RoutineResponseSerializer,
            401: "Unauthorized",
            404: "Routine not found",
        },
        tags=["Skin-Intelligence"]
    )
    def get(self, request, pk):
        routine = self.get_object(request, pk)

        serializer = RoutineResponseSerializer(routine)

        return success_response(
            message="Routine retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Update Routine",
        operation_description="Update the saved status of a routine.",
        request_body=RutineUpdateSrializer,
        responses={
            200: RoutineResponseSerializer,
            400: "Validation error",
            401: "Unauthorized",
            404: "Routine not found",
        },
        tags=["Skin-Intelligence"]
    )
    def patch(self, request, pk):
        routine = self.get_object(request, pk)

        serializer = RutineUpdateSrializer(
            routine,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = RoutineResponseSerializer(routine)

        return success_response(
            message="Routine updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )

