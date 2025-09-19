from django.contrib import admin
from .models import Plan, Order


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "members", "bot_users")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "plan__name")
