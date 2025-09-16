from django.contrib import admin
from .models import Plan, Order


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "currency", "interval", "customers", "employees")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("id", "plan__name")
