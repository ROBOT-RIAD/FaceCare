from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from account.permissions import IsUserRole
from rest_framework.permissions import  AllowAny
from .serializers import UserdataSerializer
from django.db.models import Count, Q
from account.models import User





# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Create your views here.
     

class Userdata(APIView):
    permission_classes = [IsUserRole]
    @swagger_auto_schema(
        operation_summary="Get User Statistics",
        operation_description=(
            "Get the logged-in user's total skin intelligence "
            "and non-cancelled order counts."
        ),
        responses={
            200: UserdataSerializer,
        },
        tags=["Profile"]
    )
    def get(self, request):

        user = User.objects.annotate(
            skin_intelligence_count=Count(
                "skin_intelligence",
                distinct=True
            ),
            order_count=Count(
                "orders",
                filter=~Q(orders__status="CANCELLED"),
                distinct=True
            )
        ).get(id=request.user.id)

        serializer = UserdataSerializer({
            "skin_intelligence_count": user.skin_intelligence_count,
            "order_count": user.order_count,
        })

        return success_response(
            message="User statistics retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    

