from django.db import models
from account.models import User
from product.models import Product
from .constants import ORDER_STATUS

# Create your models here.


class AddressUser(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="addresses",)
    address_line1 = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Address for User #{self.user_id}"



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders",null=True, blank=True)

    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=50, choices=ORDER_STATUS)
    
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    address = models.ForeignKey(AddressUser, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id}"



class OrderProduct(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="order_products",)
    product = models.ForeignKey(Product,on_delete=models.PROTECT,related_name="order_products",)
    product_json_field = models.JSONField(default=dict, blank=True)
    quantity = models.PositiveIntegerField(default=1)


    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_id} - Product #{self.product_id}"



class CheckoutAttempt(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="checkout_attempts",)
    address_id_snapshot = models.PositiveBigIntegerField()
    address_snapshot = models.JSONField(default=dict)
    products_snapshot = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=20)
    currency = models.CharField(max_length=10, default="USD")
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=30,default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("PAID", "Paid"),
            ("CANCELLED", "Cancelled"),
            ("EXPIRED", "Expired"),
            ("FAILED", "Failed"),
        ],
    )
    order = models.OneToOneField(Order,on_delete=models.SET_NULL,null=True,blank=True,related_name="checkout_attempt",)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
