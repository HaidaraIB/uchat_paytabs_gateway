from django.db import models
from django.utils import timezone


class Plan(models.Model):
    plan_id = models.CharField(primary_key=True, max_length=100)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    bot_users = models.IntegerField(null=True)
    members = models.IntegerField(null=True)
    is_yearly = models.BooleanField()

    def __str__(self):
        return f"Plan ${self.plan_id} {self.name} ({self.price})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    workspace_id = models.CharField(max_length=255, null=True)
    owner_email = models.CharField(max_length=255, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paytabs_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.plan.name} - {self.status}"


class Prices(models.Model):
    usd_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iqd_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Price {self.usd_price} USD -> {self.iqd_price} IQD"
