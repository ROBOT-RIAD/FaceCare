from django.contrib import admin
from .models import Notification
# Register your models here.


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id","title","sender_user","body","receiver_user","admin_notification","user_notification","all_user_notification","read","created_at","updated_at",)
    list_filter = ("read","admin_notification","user_notification","all_user_notification","created_at",)

    search_fields = ("title","body","sender_user__username","receiver_user__username",)

    readonly_fields = ("created_at","updated_at",)

    ordering = ("-created_at",)

   
