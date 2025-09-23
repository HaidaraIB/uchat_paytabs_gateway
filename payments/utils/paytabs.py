from django.conf import settings

from ..models import Order

import requests
import json


def create_pay_page(order: Order):
    endpoint = f"{settings.PAYTABS_DOMAIN}/payment/request"

    payload = {}
    payload = {
        "profile_id": int(settings.PAYTABS_PROFILE_ID),
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": str(order.id),
        "cart_description": f"{order.owner_email}-{order.workspace_id}-{order.plan.plan_id}",
        "cart_currency": "IQD",
        "cart_amount": float(order.amount),
        "callback": f"{settings.PAYTABS_CALLBACK_URL}?workspaceID={order.workspace_id}&ownerEmail={order.owner_email}",
        "return": f"{settings.PAYTABS_RETURN_URL}?workspaceID={order.workspace_id}&ownerEmail={order.owner_email}",
        "customer_details": {
            "email": order.owner_email,
        },
    }
    headers = {
        "authorization": settings.PAYTABS_SERVER_KEY,
        "content-type": "application/octet-stream",
    }
    resp = requests.post(
        endpoint,
        data=json.dumps(payload),
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()


def verify_transaction(tran_ref: str):
    endpoint = f"{settings.PAYTABS_DOMAIN}/payment/query"
    payload = {
        "profile_id": int(settings.PAYTABS_PROFILE_ID),
        "tran_ref": tran_ref,
    }
    headers = {
        "authorization": settings.PAYTABS_SERVER_KEY,
        "content-type": "application/octet-stream",
    }

    resp = requests.post(
        endpoint,
        data=json.dumps(payload),
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()
