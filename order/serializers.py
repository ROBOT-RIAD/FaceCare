from rest_framework import serializers
from .models import Order, OrderProduct, AddressUser,CheckoutAttempt
from payment.models import Payment
from django.db import transaction
from django.conf import settings
import stripe
from product.models import Product
from decimal import Decimal
from django.utils import timezone
import time
expires_at=int(time.time()) + 1800,

stripe.api_key = settings.STRIPE_SECRET_KEY

class AddressCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = AddressUser
        fields = ['address_line1', 'country', 'state', 'city', 'zip_code', 'phone_number']

    def validate(self, attrs):
        address_line1 = attrs.get('address_line1')
        country = attrs.get('country')
        state = attrs.get('state')
        city = attrs.get('city')
        zip_code = attrs.get('zip_code')
        phone_number = attrs.get('phone_number')

        if not country:
            raise serializers.ValidationError({"country": "Country is required."})
        if not state:
            raise serializers.ValidationError({"state": "State is required."})
        if not city:
            raise serializers.ValidationError({"city": "City is required."})
        if not zip_code:
            raise serializers.ValidationError({"zip_code": "Zip code is required."})
        if not phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number is required."})

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        address = AddressUser.objects.create(user=user, **validated_data)
        return address

   

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressUser
        fields = ['id',"user", 'address_line1', 'country', 'state', 'city', 'zip_code', 'phone_number']




class OrderProductInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)



class OrderCreateSerializer(serializers.ModelSerializer):
    address_id = serializers.IntegerField(write_only=True)
    products = OrderProductInputSerializer(many=True)
    shipping_fee = serializers.DecimalField(max_digits=10,decimal_places=2,min_value=Decimal("0.00"))
    payment_type = serializers.ChoiceField(choices=["COD", "ONLINE"])

    class Meta:
        model = Order
        fields = ["address_id","products","shipping_fee","payment_type"]

    def validate(self , attrs):
        user = self.context["request"].user
        items = attrs["products"]

        try:
            attrs["address"] = AddressUser.objects.get(
                id=attrs["address_id"],
                user=user,
            )
        except AddressUser.DoesNotExist:
            raise serializers.ValidationError({
                "address_id": "Invalid delivery address."
            })

        if not items:
            raise serializers.ValidationError({
                "products": "At least one product is required."
            })

        product_ids = [item["product_id"] for item in items]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError({
                "products": "Duplicate product IDs are not allowed."
            })

        products = Product.objects.in_bulk(product_ids)

        if len(products) != len(product_ids):
            raise serializers.ValidationError({
                "products": "One or more products do not exist."
            })

        for item in items:
            product = products[item["product_id"]]

            if not product.is_available:
                raise serializers.ValidationError({
                    "products": f"{product.title} is unavailable."
                })

            available_stock = product.stock - product.reserved_stock

            if item["quantity"] > available_stock:
                raise serializers.ValidationError({
                    "products": f"Insufficient stock for {product.title}."
                })

        attrs["product_objects"] = products
        return attrs

        

    def create(self , validated_data):
        user = self.context["request"].user
        payment_type = validated_data["payment_type"]
        items = validated_data["products"]
        address = validated_data["address"]
        shipping_fee = validated_data["shipping_fee"]
        product_ids = [item["product_id"] for item in items]

        with transaction.atomic():
            products = {
                p.id: p
                for p in Product.objects.select_for_update()
                .filter(id__in=product_ids)
                .order_by("id")
            }

            if len(products) != len(product_ids):
                raise serializers.ValidationError({
                    "products": "A product no longer exists."
                })


            subtotal = Decimal("0.00")
            discount_amount = Decimal("0.00")
            snapshot = []

            for item in items:
                product = products[item["product_id"]]
                quantity = item["quantity"]

                available_stock = product.stock - product.reserved_stock

                if (
                    not product.is_available
                    or quantity > available_stock
                ):
                    raise serializers.ValidationError({
                        "products": f"Insufficient stock for {product.title}."
                    })

                price = product.price

                # Assumes discount is a percentage.
                unit_discount = (
                    price * product.discount / Decimal("100")
                ).quantize(Decimal("0.01"))

                final_unit_price = price - unit_discount

                subtotal += price * quantity
                discount_amount += unit_discount * quantity

                snapshot.append({
                    "product_id": product.id,
                    "title": product.title,
                    "sku": product.sku,
                    "size": product.size,
                    "quantity": quantity,
                    "price": str(price),
                    "discount_price": str(unit_discount),
                    "final_unit_price": str(final_unit_price),
                    "image": product.image,
                })

            total_price = subtotal - discount_amount + shipping_fee

            if total_price <= 0:
                raise serializers.ValidationError({
                    "products": "Order total must be greater than zero."
                })

            if payment_type == "ONLINE":
                attempt = CheckoutAttempt.objects.create(
                    user=user,
                    address_id_snapshot=address.id,
                    address_snapshot={
                        "address_line1": address.address_line1,
                        "country": address.country,
                        "state": address.state,
                        "city": address.city,
                        "zip_code": address.zip_code,
                        "phone_number": address.phone_number,
                    },
                    products_snapshot=snapshot,
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    shipping_fee=shipping_fee,
                    total_price=total_price,
                    payment_type="ONLINE",
                    currency="USD",
                )

                # Reserve stock until payment, cancellation or expiry.
                for item in items:
                    product = products[item["product_id"]]
                    product.reserved_stock += item["quantity"]
                    product.save(update_fields=["reserved_stock"])

            else:
                # COD: create the Order immediately.
                order = Order.objects.create(
                    user=user,
                    address=address,
                    total_price=total_price,
                    discount_amount=discount_amount,
                    shipping_fee=shipping_fee,
                    status="PENDING",
                )

                for item in snapshot:
                    product = products[item["product_id"]]

                    OrderProduct.objects.create(
                        order=order,
                        product=product,
                        quantity=item["quantity"],
                        price=Decimal(item["price"]),
                        discount_price=Decimal(item["discount_price"]),
                        product_json_field={
                            "title": item["title"],
                            "sku": item["sku"],
                            "size": item["size"],
                            "image": item["image"],
                        },
                    )

                    product.reserved_stock += item["quantity"]
                    product.save(update_fields=["reserved_stock"])

                Payment.objects.create(
                    order=order,
                    amount=total_price,
                    payment_type="COD",
                    status="UNPAID",
                    currency="USD",
                )

                return order

        # ONLINE: create Stripe Checkout Session outside DB transaction.
        line_items = []

        for item in snapshot:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item["title"],
                    },
                    "unit_amount": int(
                        Decimal(item["final_unit_price"]) * 100
                    ),
                },
                "quantity": item["quantity"],
            })

        if shipping_fee > 0:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Shipping fee",
                    },
                    "unit_amount": int(shipping_fee * 100),
                },
                "quantity": 1,
            })

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=line_items,
                success_url=(
                    f"{settings.FRONTEND_SUCCESS_URL}"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=(
                    f"{settings.FRONTEND_CANCEL_URL}"
                    f"?attempt_id={attempt.id}"
                ),
                client_reference_id=str(attempt.id),
                metadata={
                    "checkout_attempt_id": str(attempt.id),
                    "user_id": str(user.id),
                },
                expires_at=int(time.time()) + 1800,
                idempotency_key=f"checkout-attempt-{attempt.id}",
            )

            attempt.stripe_session_id = session.id
            attempt.save(update_fields=[
                "stripe_session_id",
                "updated_at",
            ])

            return {
                "checkout_url": session.url,
                "checkout_attempt_id": attempt.id,
            }

        except stripe.error.StripeError:
            # Release reserved stock if Stripe session creation fails.
            with transaction.atomic():
                attempt = CheckoutAttempt.objects.select_for_update().get(
                    id=attempt.id
                )

                if attempt.status == "PENDING":
                    locked_products = {
                        p.id: p
                        for p in Product.objects.select_for_update()
                        .filter(id__in=product_ids)
                        .order_by("id")
                    }

                    for item in snapshot:
                        product = locked_products.get(item["product_id"])

                        if product:
                            product.reserved_stock = max(
                                0,
                                product.reserved_stock - item["quantity"],
                            )
                            product.save(update_fields=["reserved_stock"])

                    attempt.status = "FAILED"
                    attempt.save(update_fields=["status", "updated_at"])

            raise serializers.ValidationError({
                "payment": "Unable to start Stripe Checkout. Please try again."
            })



class OrderCheckoutSerializer(serializers.Serializer):
    url = serializers.URLField(source="checkout_url", read_only=True)
    checkout_attempt_id = serializers.IntegerField(read_only=True)



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = "__all__"



class Orderserializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source="user.email",read_only=True,allow_null=True)
    order_products = OrderProductSerializer(many=True, read_only=True)
    payment = serializers.SerializerMethodField()
    addressDetails = AddressSerializer(source="address",read_only=True,)
    
    class Meta:
        model =Order
        fields = ["id","user_name","user_email","total_price","discount_amount","status","shipping_fee","addressDetails","order_products","payment","created_at","updated_at",]

    def get_user_name(self, obj):
        if obj.user is None:
            return None

        profile = getattr(obj.user, "profile", None)
        return profile.full_name if profile else None

    def get_payment(self, obj):
        try:
            payment = obj.payment
        except Payment.DoesNotExist:
            return None

        return PaymentSerializer(payment).data


