from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from .models import Category
from .serializers import CategoryCreateandUpdateserializer,Categorylistserializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsAdminRole,IsUserRole
from rest_framework.permissions import  AllowAny


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Create your views here.
class CategoryCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Create a new category",
        operation_description="Create a new category with the provided name and image.",
        request_body=CategoryCreateandUpdateserializer,
        responses={
            201: Categorylistserializer,
            400: 'Bad Request',
            401: 'Unauthorized',
        },
        tags=['Category']
    )
    def post(self, request):
        serializer = CategoryCreateandUpdateserializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return success_response(
            message="Category created successfully",
            data=Categorylistserializer(category, context={"request": request}).data,
            status_code=status.HTTP_201_CREATED
        )

        

class CategoryListView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="List all categories",
        operation_description="Retrieve a list of all categories.",
        responses={
            200: Categorylistserializer(many=True),
            401: 'Unauthorized',
        },
        tags=['Category']
    )
    def get(self, request):
        categories = Category.objects.all().order_by("created_at")
        serializer = Categorylistserializer(categories, many=True)
        return success_response(data=serializer.data,message="Category list fetched successfully",status_code=status.HTTP_200_OK)



class CategoryRetriveApi(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Retrieve a category by ID",
        operation_description="Retrieve a category by its ID.",
        responses={
            200: Categorylistserializer,
            404: 'Not Found',
            401: 'Unauthorized',
        },
        tags=['Category']
    )
    def get(self , request , pk ,*args , **kwargs):
        category = Category.objects.get(pk=pk)
        serializer = Categorylistserializer(category)
        return success_response(data=serializer.data,message="Category fetched successfully",status_code=status.HTTP_200_OK)



class CategoryUpdateDeleteApi(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAdminRole]
    @swagger_auto_schema(
        operation_summary="Update a category by ID",
        operation_description="Update a category by its ID.",
        request_body=CategoryCreateandUpdateserializer,
        responses={
            200: Categorylistserializer,
            400: 'Bad Request',
            404: 'Not Found',
            401: 'Unauthorized',
        },
        tags=['Category']
    )
    def patch(self , request , pk ,*args , **kwargs):
        category = Category.objects.get(pk=pk)
        serializer = CategoryCreateandUpdateserializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        category=serializer.save()

        return success_response(data=Categorylistserializer(category).data,message="Category updated successfully",status_code=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete a category by ID",
        operation_description="Delete a category by its ID.",
        responses={
            204: 'No Content',
            404: 'Not Found',
            401: 'Unauthorized',
        },
        tags=['Category']
    )
    def delete(self , request , pk ,*args , **kwargs):
        category = Category.objects.get(pk=pk)
        category.delete()
        return success_response(message="Category deleted successfully",status_code=status.HTTP_204_NO_CONTENT)