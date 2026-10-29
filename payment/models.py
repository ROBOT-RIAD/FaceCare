from django.db import models
from order.models import Order
from .constants import PAYMENT_STATUS,PAYMENT_TYPE
# Create your models here.

class Payment(models.Model):
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name="payment",)

    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS,default="UNPAID")
    paid_at = models.DateTimeField(blank=True, null=True)

    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)

    currency = models.CharField(max_length=10, default="USD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order_id}"
