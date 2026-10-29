from django.shortcuts import render
from rest_framework.views import APIView
from backend.response import success_response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from account.permissions import IsUserRole
from .models import AddressUser,Order,OrderProduct,CheckoutAttempt
from product.models import Product
from payment.models import Payment
from .serializers import AddressCreateSerializer,AddressSerializer,OrderCreateSerializer,OrderCheckoutSerializer,Orderserializer
from django.shortcuts import get_object_or_404

import json
import stripe
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.utils.decorators import method_decorator


# swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class AddressCreateView(APIView):
    permission_classes = [IsUserRole]
    parser_classes = [MultiPartParser, FormParser]
    @swagger_auto_schema(
        operation_summary="Create a new address",
        operation_description="Create a new address for the authenticated user.",
        request_body=AddressCreateSerializer,
        responses={
            201: AddressSerializer,
            400: 'Bad Request',
            401: 'Unauthorized',
        },
        tags=['Address']
    )
    def post(self, request):
        serializer = AddressCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return success_response(
            message="Address created successfully",
            data=AddressSerializer(address).data,
            status_code=status.HTTP_201_CREATED
        )



class AddressListView(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="List all addresses for the authenticated user",
        operation_description="Retrieve a list of all addresses associated with the authenticated user.",
        responses={
            200: AddressSerializer(many=True),
            401: 'Unauthorized',
        },
        tags=['Address']
    )
    def get(self, request):
        user = request.user
        addresses = AddressUser.objects.filter(user=user)
        serializer = AddressSerializer(addresses, many=True)
        return success_response(
            message="Addresses retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )



class AddressDetailandDeleteView(APIView):
    permission_classes = [IsUserRole]

    @swagger_auto_schema(
        operation_summary="Retrieve a specific address",
        operation_description="Retrieve details of a specific address by its ID.",
        responses={
            200: AddressSerializer,
            404: 'Not Found',
            401: 'Unauthorized',
        },
        tags=['Address']
    )
    def get(self, request, pk):
        user = request.user
        try:
            address = AddressUser.objects.get(id=pk, user=user)
        except AddressUser.DoesNotExist:
            return success_response(
                message="Address not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = AddressSerializer(address)
        return success_response(
            message="Address retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete a specific address",
        operation_description="Delete a specific address by its ID.",
        responses={
            204: 'No Content',
            404: 'Not Found',
            401: 'Unauthorized',
        },
        tags=['Address']
    )
    def delete(self, request, pk):
        user = request.user
        try:
            address = AddressUser.objects.get(id=pk, user=user)
        except AddressUser.DoesNotExist:
            return success_response(
                message="Address not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        address.delete()
        return success_response(
            message="Address deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )



class OrderCreateAPIView(APIView):
    permission_classes=[IsUserRole]
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        operation_summary="create Order COD or ONLINE",
        operation_description="create Order COD or ONLINE",
        request_body=OrderCreateSerializer,
        responses={
            201: openapi.Response(
                description=(
                    "ONLINE returns checkout URL and attempt ID. "
                    "COD returns the created order."
                ),
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT
                        ),
                    },
                ),
            ),
            400: "Bad Request",
            401: "Unauthorized",
        },
        tags=['Order']
    )
    def post(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data,context={"request": request},)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        if serializer.validated_data["payment_type"] == "ONLINE":
            response_serializer = OrderCheckoutSerializer(
                instance=result
            )
            message = "Checkout session created successfully"
        else:
            response_serializer = Orderserializer(
                instance=result,
                context={"request": request},
            )
            message = "Order created successfully"

        return success_response(
            message=message,
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )



@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookAPIView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Handle Stripe webhook",
        operation_description=(
            "Verify Stripe webhook events, process successful payments, "
            "create orders, update stock, and release reserved stock "
            "when checkout expires or payment fails."
        ),
        tags=["Web hook"],
    )
    def post(self, request):

        # 1. Get Stripe webhook payload and signature
        payload = request.body
        signature = request.headers.get("Stripe-Signature")

        # 2. Verify the Stripe webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (
            ValueError,
            stripe.error.SignatureVerificationError,
        ):
            return HttpResponse(status=400)

        event_type = event["type"]
        session = event["data"]["object"].to_dict()

        # 3. Handle successful payment events
        if event_type in (
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
        ):

            # Do not create an order unless payment is paid
            if session.get("payment_status") != "paid":
                return success_response(
                    message="Payment is not completed yet.",
                    status_code=200,
                )

            attempt_id = session.get("metadata", {}).get(
                "checkout_attempt_id"
            )

            if not attempt_id:
                return HttpResponse(status=400)

            try:
                with transaction.atomic():

                    attempt = (
                        CheckoutAttempt.objects
                        .select_for_update()
                        .get(
                            id=attempt_id,
                            stripe_session_id=session["id"],
                        )
                    )

                    # Prevent duplicate order creation
                    if attempt.status == "PAID" and attempt.order_id:
                        return success_response(
                            message="Payment already processed.",
                            status_code=200,
                        )

                    if attempt.status != "PENDING":
                        return success_response(
                            message="Checkout attempt is not pending.",
                            status_code=200,
                        )

                    # Get product IDs from checkout snapshot
                    product_ids = [
                        item["product_id"]
                        for item in attempt.products_snapshot
                    ]

                    # Lock products to prevent stock race conditions
                    products = {
                        product.id: product
                        for product in (
                            Product.objects.select_for_update()
                            .filter(id__in=product_ids)
                            .order_by("id")
                        )
                    }

                    if len(products) != len(product_ids):
                        raise ValueError(
                            "A checkout product no longer exists."
                        )

                    # Validate reserved stock
                    for item in attempt.products_snapshot:
                        product = products[item["product_id"]]

                        if product.reserved_stock < item["quantity"]:
                            raise ValueError(
                                "Stock reservation is inconsistent."
                            )

                    # Get the checkout address
                    address = None

                    try:
                        address = AddressUser.objects.get(
                            id=attempt.address_id_snapshot,
                            user=attempt.user,
                        )
                    except AddressUser.DoesNotExist:
                        pass

                    # Create order
                    order = Order.objects.create(
                        user=attempt.user,
                        address=address,
                        total_price=attempt.total_price,
                        discount_amount=attempt.discount_amount,
                        shipping_fee=attempt.shipping_fee,
                        status="PENDING",
                    )

                    # Create order items and update stock
                    for item in attempt.products_snapshot:
                        product = products[item["product_id"]]
                        quantity = item["quantity"]

                        OrderProduct.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=item["price"],
                            discount_price=item["discount_price"],
                            product_json_field={
                                "title": item["title"],
                                "sku": item["sku"],
                                "image": item.get("image"),
                            },
                        )

                        # Convert reserved stock to sold stock
                        product.stock -= quantity
                        product.reserved_stock -= quantity

                        product.save(
                            update_fields=[
                                "stock",
                                "reserved_stock",
                            ]
                        )

                    # Create payment record
                    payment_intent_id = str(
                        session.get("payment_intent") or ""
                    )

                    Payment.objects.create(
                        order=order,
                        amount=attempt.total_price,
                        payment_type="ONLINE",
                        status="PAID",
                        transaction_id=payment_intent_id,
                        stripe_payment_intent_id=payment_intent_id,
                        currency=attempt.currency,
                        paid_at=timezone.now(),
                    )

                    # Mark checkout attempt as paid
                    attempt.status = "PAID"
                    attempt.order = order

                    attempt.save(
                        update_fields=[
                            "status",
                            "order",
                            "updated_at",
                        ]
                    )

            except CheckoutAttempt.DoesNotExist:
                return HttpResponse(status=400)

        # 4. Handle expired checkout or failed payment
        elif event_type in (
            "checkout.session.expired",
            "checkout.session.async_payment_failed",
        ):

            attempt_id = session.get("metadata", {}).get(
                "checkout_attempt_id"
            )

            if attempt_id:
                with transaction.atomic():

                    try:
                        attempt = (
                            CheckoutAttempt.objects
                            .select_for_update()
                            .get(
                                id=attempt_id,
                                stripe_session_id=session["id"],
                            )
                        )
                    except CheckoutAttempt.DoesNotExist:
                        return success_response(
                            message="Checkout attempt not found.",
                            status_code=200,
                        )

                    if attempt.status == "PENDING":

                        product_ids = [
                            item["product_id"]
                            for item in attempt.products_snapshot
                        ]

                        products = {
                            product.id: product
                            for product in (
                                Product.objects.select_for_update()
                                .filter(id__in=product_ids)
                                .order_by("id")
                            )
                        }

                        # Release reserved stock
                        for item in attempt.products_snapshot:
                            product = products.get(
                                item["product_id"]
                            )

                            if product:
                                product.reserved_stock = max(
                                    0,
                                    product.reserved_stock
                                    - item["quantity"],
                                )

                                product.save(
                                    update_fields=["reserved_stock"]
                                )

                        # Update checkout attempt status
                        if event_type == "checkout.session.expired":
                            attempt.status = "EXPIRED"
                        else:
                            attempt.status = "FAILED"

                        attempt.save(
                            update_fields=[
                                "status",
                                "updated_at",
                            ]
                        )

        # 5. Return success to Stripe
        return success_response(
            message="Stripe webhook processed successfully.",
            status_code=status.HTTP_200_OK,
        )
        


class CheckoutPaymentStatusAPIView(APIView):
    permission_classes=[IsUserRole]
    @swagger_auto_schema(
        operation_summary="Get Checkout Payment Status",
        operation_description=(
            "Retrieve the Stripe payment status and the associated "
            "checkout attempt, order, and payment information "
            "using the Stripe Checkout Session ID."
        ),
        manual_parameters=[
            openapi.Parameter(
                name="session_id",
                in_=openapi.IN_QUERY,
                description="Stripe Checkout Session ID",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Payment status retrieved successfully."
            ),
            400: openapi.Response(
                description="Missing or invalid session ID."
            ),
            401: openapi.Response(
                description="Authentication required."
            ),
            403: openapi.Response(
                description="Permission denied."
            ),
            404: openapi.Response(
                description="Checkout attempt not found."
            ),
            502: openapi.Response(
                description="Unable to verify payment with Stripe."
            ),
        },
        tags=['Order']
    )
    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return success_response(
                success= False,
                message ="session_id is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        attempt = get_object_or_404(
            CheckoutAttempt.objects.select_related("order"),
            stripe_session_id=session_id,
            user=request.user,
        )

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY

            session = stripe.checkout.Session.retrieve(
                attempt.stripe_session_id
            )

        except stripe.StripeError:
        
            return success_response(
                success= False,
                message= "Unable to verify payment with Stripe.",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )

        # Verify the retrieved session
        if session.id != attempt.stripe_session_id:
            return success_response(
              
                success= False,
                message= "Invalid checkout session.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        order = attempt.order
        payment = (
            Payment.objects.filter(order=order).first()
            if order
            else None
        )

        data = {
            "session_id": session.id,
            "stripe_payment_status": session.payment_status,
            "checkout_attempt_status": attempt.status,
            "order_id": order.id if order else None,
            "order_status": order.status if order else None,
            "payment_status": payment.status if payment else None,
            "total_price": str(attempt.total_price),
            "currency": attempt.currency,
            "webhook_processed": (
                attempt.status == "PAID"
                and order is not None
                and payment is not None
            ),
        }

        return success_response(
            message= "Payment status retrieved successfully.",
            data=data,
            status_code=status.HTTP_200_OK,
        )




