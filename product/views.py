from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsAdminRole,IsUserRole
from rest_framework.permissions import  AllowAny


from .models import Product
from .serializers import ProductCreateUpdateSerializer,Productserializer


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class ProductCreateView(APIView):
    parser_classes=[MultiPartParser,FormParser]
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="get all products",
        operation_description="Endpoint to create a new product. Only accessible by admin users.",
        request_body=ProductCreateUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Product created successfully",
                schema=Productserializer
            ),
            400: 'Bad Request',
            401: 'Unauthorized',
        },
        tags=['Product']
    )
    def post(self,request ,*args, **kwargs):
        serializer = ProductCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return success_response(
                message="Category created successfully",
                data=Productserializer(product, context={"request": request}).data,
                status_code=status.HTTP_201_CREATED
            )




class ProductListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="List all Product",
        operation_description="Retrieve a list of all Product.",
        responses={
            200: Productserializer(many=True),
            401: 'Unauthorized',
        },
        tags=['Product']
    )
    def get(self, request,*args, **kwargs):
        products = Product.objects.select_related("category").order_by("created_at")
        serializer = Productserializer(products, many=True)
        return success_response(data=serializer.data,message="Products list fetched successfully",status_code=status.HTTP_200_OK)
       




