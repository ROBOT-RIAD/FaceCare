from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id","order","payment_type","amount","currency","status","transaction_id","paid_at","created_at",)

    list_display_links = ("id", "order")

    list_filter = ("payment_type","status","currency","created_at","paid_at",)

    search_fields = ("order__id","transaction_id","stripe_payment_intent_id","stripe_payment_method_id","order__user__email","order__user__username",)

    readonly_fields = ("created_at","updated_at",)

    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Payment Information",
            {
                "fields": (
                    "order",
                    "payment_type",
                    "amount",
                    "currency",
                    "status",
                    "paid_at",
                )
            },
        ),
        (
            "Transaction Details",
            {
                "fields": (
                    "transaction_id",
                    "stripe_payment_intent_id",
                    "stripe_payment_method_id",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
