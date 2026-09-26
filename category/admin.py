from django.contrib import admin
from .models import Category

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id","name","image","cloudinary_public_id","created_at","updated_at",)
    search_fields = ("name",)
    list_filter = ("created_at","updated_at",)
    readonly_fields = ("created_at","updated_at",)
    ordering = ("-created_at",)
