from django.db import models
from django.utils import timezone


class Plan(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    currency = models.CharField(max_length=8, default="USD")
    interval = models.CharField(max_length=20, default="monthly", blank=True)
    customers = models.IntegerField(null=True)
    employees = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    created_at = models.DateTimeField(default=timezone.now)
    paytabs_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.plan.name} - {self.status}"
