from django.contrib import admin
from .models import User,Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id","username", "email", "role", "is_staff", "is_active"]
    search_fields =["email", "username"]
    list_filter =["role", "is_staff", "is_active"]

    ordering = ["-id"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "password",
                )
            },
        ),
        (
            "User Information",
            {
                "fields": (
                    "role",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id","user","user__email","full_name","gender","contact_number","skin_type","date_of_birth","image","created_at","updated_at" ]
    search_fields = ["user__email", "full_name","contact_number"]
    list_filter = ["created_at",]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Email")
    def user_email(self, obj):
        return obj.user.email






