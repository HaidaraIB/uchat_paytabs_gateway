import requests
from django.conf import settings


def create_pay_page(order, customer):
    endpoint = f"{settings.PAYTABS_DOMAIN}/payment/request"

    payload = {
        "merchant_email": settings.PAYTABS_MERCHANT_EMAIL,
        "secret_key": settings.PAYTABS_SECRET_KEY,
        "site_url": settings.PAYTABS_RETURN_URL,
        "return_url": settings.PAYTABS_RETURN_URL,
        "cc_first_name": customer.get("first_name"),
        "cc_last_name": customer.get("last_name"),
        "cc_email": customer.get("email"),
        "phone_number": customer.get("phone"),
        "products_per_title": order.plan.name,
        "amount": str(order.amount),
        "currency": order.currency,
        "callback": settings.PAYTABS_CALLBACK_URL,
        "custom_payment_name": f"UChat-{order.id}",
    }

    resp = requests.post(endpoint, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def verify_transaction(tran_ref: str):
    """
    Verify transaction by transaction reference.
    Docs: PayTabs PT2 Transaction API
    """
    endpoint = f"{settings.PAYTABS_DOMAIN}/payment/query"

    payload = {
        "merchant_email": settings.PAYTABS_MERCHANT_EMAIL,
        "secret_key": settings.PAYTABS_SECRET_KEY,
        "tran_ref": tran_ref,
    }

    resp = requests.post(endpoint, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()
