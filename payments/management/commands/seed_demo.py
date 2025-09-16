from django.core.management.base import BaseCommand
from payments.models import Plan, Order
from decimal import Decimal


class Command(BaseCommand):
    help = "Seed demo plans and sample orders for payments app"

    def handle(self, *args, **options):
        plans = [
            {
                "slug": "free",
                "name": "Free",
                "price": Decimal("0.00"),
                "currency": "USD",
                "interval": "14 day",
                "customers": 200,
                "employees": 1,
            },
            {
                "slug": "business",
                "name": "Business",
                "price": Decimal("39.00"),
                "currency": "USD",
                "interval": "monthly",
                "customers": 1000,
                "employees": 5,
            },
            {
                "slug": "pro",
                "name": "Pro",
                "price": Decimal("99.00"),
                "currency": "USD",
                "interval": "monthly",
                "customers": 10_000,
                "employees": 5,
            },
        ]

        created = 0
        for p in plans:
            obj, was_created = Plan.objects.update_or_create(
                slug=p["slug"],
                defaults={
                    "name": p["name"],
                    "price": p["price"],
                    "currency": p["currency"],
                    "interval": p["interval"],
                    "customers": p["customers"],
                    "employees": p["employees"],
                },
            )
            if was_created:
                created += 1

        # create a couple of demo orders (pending)
        if not Order.objects.filter(plan__slug="free").exists():
            basic = Plan.objects.get(slug="free")
            Order.objects.create(
                plan=basic,
                amount=basic.price,
                currency=basic.currency,
                status="pending",
            )
        if not Order.objects.filter(plan__slug="pro").exists():
            pro = Plan.objects.get(slug="pro")
            Order.objects.create(
                plan=pro, amount=pro.price, currency=pro.currency, status="pending"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Seed complete — created/updated {len(plans)} plans.")
        )
