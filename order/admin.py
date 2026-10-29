from django.contrib import admin

# Register your models here.
from .models import AddressUser, Order, OrderProduct,CheckoutAttempt


@admin.register(AddressUser)
class AddressUserAdmin(admin.ModelAdmin):
    list_display = ("id","user","phone_number","city","state","country",)
    list_display_links = ("id", "user")
    list_filter = ("country", "state", "city")
    search_fields = ("user__email","user__username","phone_number","city","zip_code",)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("product","quantity","price","discount_price","product_json_field","created_at","updated_at",)




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id","user","total_price","discount_amount","shipping_fee","status","created_at",)
    list_display_links = ("id",)
    list_filter = ("status", "created_at")
    search_fields = ("id","user__email","user__username","address__phone_number","address__city","address__state","address__country",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderProductInline]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ("id","order","product","quantity","price","discount_price","created_at", )
    list_display_links = ("id", "order")
    list_filter = ("created_at",)
    search_fields = ("order__id","product__title","product__sku",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)




@admin.register(CheckoutAttempt)
class CheckoutAttemptAdmin(admin.ModelAdmin):
    list_display = ("id","user","total_price","currency","status","stripe_session_id","order","created_at",)
    list_filter = ("status","payment_type","currency","created_at",)
    search_fields = ("user__email","stripe_session_id","order__id",)
    readonly_fields = ("user","address_id_snapshot","address_snapshot","products_snapshot","subtotal","discount_amount","shipping_fee","total_price","payment_type","currency","stripe_session_id","status","order","created_at","updated_at",)
    ordering = ("-created_at",)