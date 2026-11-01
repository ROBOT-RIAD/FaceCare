from django.shortcuts import render
from decimal import Decimal

from django.db.models import Count, Sum, Q,F, DecimalField

from rest_framework.views import APIView
from rest_framework import status

from account.permissions import IsAdminRole
from backend.response import success_response

from order.models import Order, CheckoutAttempt
from payment.models import Payment

from .serializers import AdminAnotdSerializer,AdminMonthlyRevenueSerializer,AdminMonthlyRevenueQuerySerializer,AdminLastSevenDaysOrderSerializer,AdminBestSellingProductSerializer,AdminUserSerializer


import calendar

from datetime import date, datetime, time


from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta

from django.shortcuts import get_object_or_404



from account.models import User



from order.models import OrderProduct
from rest_framework.pagination import PageNumberPagination




from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.



class AdminDashboardStatistics(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Get Admin Dashboard Statistics",
        operation_description=(
            "Retrieve total revenue, total non-cancelled orders, "
            "total customers and checkout conversion rate."
        ),
        responses={
            200: AdminAnotdSerializer,
            401: "Unauthorized",
        },
        tags=["Admin Dashboard"]
    )
    def get(self, request):

        # STEP 1: Total Revenue
        revenue = Payment.objects.filter(
            status="PAID"
        ).aggregate(
            total_revenue=Sum("amount")
        )

        total_revenue = revenue["total_revenue"] or Decimal("0.00")


        # STEP 2: Total Orders (Exclude Cancelled)
        order_stats = Order.objects.exclude(
            status="CANCELLED"
        ).aggregate(
            total_orders=Count("id")
        )

        total_orders = order_stats["total_orders"]


        # STEP 3: Total Customers
        customer_stats = Order.objects.exclude(
            status="CANCELLED"
        ).exclude(
            user__isnull=True
        ).values(
            "user_id"
        ).annotate(
            order_count=Count("id")
        ).filter(
            order_count__gt=0
        ).aggregate(
            total_customers=Count("user_id")
        )

        total_customers = customer_stats["total_customers"]


        # STEP 4: Checkout Conversion Rate
        checkout_stats = CheckoutAttempt.objects.aggregate(
            total_attempts=Count("id"),
            successful_attempts=Count(
                "id",
                filter=Q(status="PAID")
            )
        )

        total_attempts = checkout_stats["total_attempts"]
        successful_attempts = checkout_stats["successful_attempts"]

        if total_attempts > 0:
            conversion_rate = (
                Decimal(successful_attempts)
                / Decimal(total_attempts)
            ) * Decimal("100")
        else:
            conversion_rate = Decimal("0.00")


        # STEP 5: Response Data
        data = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "conversion_rate": conversion_rate,
        }

        serializer = AdminAnotdSerializer(data)

        return success_response(
            message="Admin dashboard statistics retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )





class AdminMonthlyRevenueAPIView(APIView):
    permission_classes = [IsAdminRole]

    def get_month_revenue(self, year, month):

        first_day = date(year, month, 1)

        last_day = date(
            year,
            month,
            calendar.monthrange(year, month)[1]
        )

        current_tz = timezone.get_current_timezone()

        start_datetime = timezone.make_aware(
            datetime.combine(first_day, time.min),
            current_tz
        )

        next_month_year = year + (1 if month == 12 else 0)
        next_month = 1 if month == 12 else month + 1

        end_datetime = timezone.make_aware(
            datetime.combine(
                date(next_month_year, next_month, 1),
                time.min
            ),
            current_tz
        )

        # Daily revenue using annotate
        daily_data = Payment.objects.filter(
            status="PAID",
            paid_at__gte=start_datetime,
            paid_at__lt=end_datetime
        ).annotate(
            payment_date=TruncDate(
                "paid_at",
                tzinfo=current_tz
            )
        ).values(
            "payment_date"
        ).annotate(
            revenue=Sum("amount")
        ).order_by(
            "payment_date"
        )

        # Convert queryset into dictionary
        revenue_dict = {
            item["payment_date"]: item["revenue"]
            for item in daily_data
        }

        # Generate every day, including zero-revenue days
        daily_revenue = []

        for day in range(1, last_day.day + 1):

            current_date = date(year, month, day)

            daily_revenue.append({
                "day": day,
                "date": current_date,
                "revenue": revenue_dict.get(
                    current_date,
                    Decimal("0.00")
                )
            })

        # Monthly total
        total_revenue = sum(
            revenue_dict.values(),
            Decimal("0.00")
        )

        return {
            "month": first_day.strftime("%B %Y"),
            "total_revenue": total_revenue,
            "daily_revenue": daily_revenue
        }

    @swagger_auto_schema(
        operation_summary="Get Monthly Revenue Comparison",
        operation_description=(
            "Get daily revenue for a selected month and its previous month. "
            "Defaults to the current month and previous month."
        ),
        manual_parameters=[
            openapi.Parameter(
                "year",
                openapi.IN_QUERY,
                description="Year (e.g. 2026)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                "month",
                openapi.IN_QUERY,
                description="Month (1-12)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: AdminMonthlyRevenueSerializer,
            400: "Invalid year or month",
            401: "Unauthorized",
        },
        tags=["Admin Dashboard"]
    )
    def get(self, request):

        # Validate query parameters
        query_serializer = AdminMonthlyRevenueQuerySerializer(
            data=request.query_params
        )

        if not query_serializer.is_valid():
            return Response(
                query_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        params = query_serializer.validated_data

        today = timezone.localdate()

        year = params.get("year", today.year)
        month = params.get("month", today.month)

        # Previous month calculation
        if month == 1:
            previous_year = year - 1
            previous_month = 12
        else:
            previous_year = year
            previous_month = month - 1

        # Selected month revenue
        selected_month_data = self.get_month_revenue(
            year,
            month
        )

        # Previous month revenue
        previous_month_data = self.get_month_revenue(
            previous_year,
            previous_month
        )

        data = {
            "selected_month": selected_month_data,
            "previous_month": previous_month_data
        }

        serializer = AdminMonthlyRevenueSerializer(data)

        return success_response(
            message="Monthly revenue retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )





class AdminLastSevenDaysOrderAPIView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Get Last 7 Days Order Statistics",
        operation_description=(
            "Get daily non-cancelled order counts for the last 7 days, "
            "including today."
        ),
        responses={
            200: AdminLastSevenDaysOrderSerializer(many=True),
            401: "Unauthorized",
        },
        tags=["Admin Dashboard"]
    )
    def get(self, request):

        today = timezone.localdate()
        start_date = today - timedelta(days=6)

        current_tz = timezone.get_current_timezone()

        # Get daily order counts
        order_data = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today,
        ).exclude(
            status="CANCELLED"
        ).annotate(
            order_date=TruncDate(
                "created_at",
                tzinfo=current_tz
            )
        ).values(
            "order_date"
        ).annotate(
            order_count=Count("id")
        ).order_by(
            "order_date"
        )

        # Convert queryset to dictionary
        order_dict = {
            item["order_date"]: item["order_count"]
            for item in order_data
        }

        # Generate all 7 days
        daily_orders = []

        for i in range(7):

            current_date = start_date + timedelta(days=i)

            daily_orders.append({
                "date": current_date,
                "day": current_date.strftime("%A"),
                "order_count": order_dict.get(
                    current_date,
                    0
                )
            })

        serializer = AdminLastSevenDaysOrderSerializer(
            daily_orders,
            many=True
        )

        return success_response(
            message="Last 7 days order statistics retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )




class AdminBestSellingProductsAPIView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Get Best Selling Products",
        operation_description=(
            "Get products with total sold quantity, "
            "total sales amount, product name and image."
        ),
        responses={
            200: AdminBestSellingProductSerializer(many=True),
            401: "Unauthorized",
        },
        tags=["Admin Dashboard"]
    )
    def get(self, request):

        products = OrderProduct.objects.exclude(
            order__status="CANCELLED"
        ).values(
            "product_id",
            "product__title",
            "product__image"
        ).annotate(
            total_sold=Sum("quantity"),

            total_sales=Sum(
                F("discount_price") * F("quantity"),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        ).order_by(
            "-total_sold"
        )

        data = [
            {
                "product_id": item["product_id"],
                "product_name": item["product__title"],
                "product_image": item["product__image"],
                "total_sold": item["total_sold"],
                "total_sales": item["total_sales"] or 0,
            }
            for item in products
        ]

        serializer = AdminBestSellingProductSerializer(
            data,
            many=True
        )

        return success_response(
            message="Best selling products retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )




class AdminUserListAPIView(APIView):
    permission_classes = [IsAdminRole]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_summary="Get All Users",
        operation_description=(
            "Admin can retrieve all normal users "
            "with their email and profile information."
        ),
        responses={
            200: AdminUserSerializer(many=True),
            401: "Unauthorized",
        },
        tags=["Admin User"]
    )
    def get(self, request):

        users = User.objects.filter(
            role="user",
            is_staff=False,
            is_superuser=False
        ).select_related(
            "profile"
        ).order_by("-date_joined")

        paginator = self.pagination_class()
        paginator.page_size = 10

        paginated_users = paginator.paginate_queryset(
            users, request, view=self
        )

        serializer = AdminUserSerializer(
            paginated_users,
            many=True
        )

        return success_response(
            message="Users retrieved successfully",
            data={
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            },
            status_code=status.HTTP_200_OK
        )




class AdminUserDeleteAPIView(APIView):
    permission_classes = [IsAdminRole]

    @swagger_auto_schema(
        operation_summary="Delete User",
        operation_description=(
            "Admin can delete a normal user. "
            "Admin and superuser accounts cannot be deleted."
        ),
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: "User deleted successfully",
            404: "User not found or cannot be deleted",
            401: "Unauthorized",
        },
        tags=["Admin User"]
    )
    def delete(self, request, user_id):

        user = get_object_or_404(
            User.objects.filter(
                role="user",
                is_staff=False,
                is_superuser=False
            ),
            id=user_id
        )

        user.delete()

        return success_response(
            message="User deleted successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )



