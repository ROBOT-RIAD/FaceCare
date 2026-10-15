from django.contrib import admin
from .models import Product
# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id","category","title","sub_title","description","key_ingredients","size","price","discount","stock","reserved_stock","is_available","skin_type","key_benefits","how_to_use","image","cloudinary_public_id","sku","created_at","updated_at",)

    list_filter = ("category","is_available","skin_type","created_at","updated_at",)

    search_fields = ("title","sub_title","description","key_ingredients","skin_type","key_benefits","how_to_use","sku","category__name",)

    ordering = ("-created_at",)

    readonly_fields = ("sku","created_at","updated_at",)

    list_editable = ("price","discount","stock","reserved_stock","is_available",)

    autocomplete_fields = ("category",)