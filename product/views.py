from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsAdminRole,IsUserRole
from rest_framework.permissions import  AllowAny
from rest_framework.pagination import PageNumberPagination


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
    pagination_class = PageNumberPagination


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
        paginator = self.pagination_class()
        paginator.page_size = 10
        paginated_products = paginator.paginate_queryset(
            products, request, view=self
        )
        serializer = Productserializer(paginated_products, many=True)
        return success_response(data={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },message="Products list fetched successfully",status_code=status.HTTP_200_OK)
       



class ProductRetriveApi(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Retrieve a Product by ID",
        operation_description="Retrieve a specific Product by its ID.",
        responses={
            200: Productserializer,
            401: 'Unauthorized',
            404: 'Not Found',
        },
        tags=['Product']
    )
    def get(self, request, pk,*args, **kwargs):
        product = Product.objects.select_related("category").get(pk=pk)
        serializer = Productserializer(product)
        return success_response(data=serializer.data,message="Product fetched successfully",status_code=status.HTTP_200_OK)




class ProductUpdateDeleteApi(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Update a Product by ID",
        operation_description="Update a specific Product by its ID.",
        request_body=ProductCreateUpdateSerializer,
        responses={
            200: Productserializer,
            400: 'Bad Request',
            401: 'Unauthorized',
            404: 'Not Found',
        },
        tags=['Product']
    )
    def patch(self, request, pk,*args,**kwargs):
        product = Product.objects.get(pk=pk)
        serializer = ProductCreateUpdateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return success_response(data=Productserializer(product).data,message="Product updated successfully",status_code=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete a Product by ID",
        operation_description="Delete a specific Product by its ID.",
        responses={
            200: 'Product deleted successfully',
            401: 'Unauthorized',
            404: 'Not Found',
        },
        tags=['Product']
    )
    def delete(self, request, pk,*args,**kwargs):
        product = Product.objects.get(pk=pk)
        product.delete()
        return success_response(message="Product deleted successfully",status_code=status.HTTP_200_OK)