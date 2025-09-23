from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages


from .models import Plan, Order, Prices
from .utils.paytabs import create_pay_page, verify_transaction
from .utils.uchat import change_plan

import requests
import logging

logger = logging.getLogger("payments")


def checkout(request):
    workspace_id = request.GET.get("workspaceID")
    owner_email = request.GET.get("ownerEmail")

    plans = requests.get(
        f"{settings.UCHAT_BASE_URL}/plans",
        headers={
            "Authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()

    if plans.get("status", False) == "ok":
        plans = plans["data"]

    for plan in plans:
        plan["price"] = int(
            Prices.objects.filter(usd_price=plan["price"]).first().iqd_price or 1000_000
        )
        p = Plan.objects.filter(pk=plan["id"])
        if p:
            p.update(
                name=plan["name"],
                price=plan["price"],
                bot_users=plan["bot_users"],
                members=plan["members"],
                is_yearly=plan["is_yearly"],
            )
        else:
            Plan.objects.create(
                plan_id=plan["id"],
                name=plan["name"],
                price=plan["price"],
                bot_users=plan["bot_users"],
                members=plan["members"],
                is_yearly=plan["is_yearly"],
            )

    current_workspace = requests.get(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}",
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()
    if current_workspace["status"] == "ok":
        current_workspace["plan"] = (
            current_workspace["data"]["plan"].replace("'", "").split(",")
        )
    else:
        current_workspace["plan"] = "free"

    return render(
        request,
        "payments/checkout.html",
        {
            "workspace_id": workspace_id,
            "owner_email": owner_email,
            "plans": plans,
            "current_workspace": current_workspace,
        },
    )


def subscribe(request, plan_id):
    workspace_id = request.GET.get("workspaceID")
    owner_email = request.GET.get("ownerEmail")
    plan = get_object_or_404(Plan, plan_id=plan_id)
    order = Order.objects.create(
        plan=plan,
        amount=plan.price,
        workspace_id=workspace_id,
        owner_email=owner_email,
    )
    logger.info("New Order: %s", order)
    if plan.price == 0:
        workspace_id = change_plan(
            owner_email=order.owner_email,
            workspace_id=order.workspace_id,
            plan_id=order.plan.plan_id,
        )
        if not workspace_id:
            # TODO error
            return
        order.workspace_id = workspace_id
        order.status = "paid"
        order.save()
        return render(request, "payments/success.html", {"order": order, "plan": plan})

    data = create_pay_page(order)
    order.raw_response = data
    order.save()

    redirect_url = (
        data.get("redirect_url") or data.get("payment_url") or data.get("payment_link")
    )
    if redirect_url:
        return redirect(redirect_url)

    return HttpResponse("Error creating payment session")


@csrf_exempt
def paytabs_return(request):
    payload = request.POST.dict() if request.method == "POST" else request.GET.dict()
    tran_ref = (
        payload.get("tran_ref")
        or payload.get("transaction_id")
        or payload.get("tranRef")
        or payload.get("transactionID")
        or payload.get("transactionId")
    )

    logger.info("PayTabs return payload: %s", payload)

    order = None
    result = None
    if tran_ref:
        try:
            result = verify_transaction(tran_ref)
            if result:
                logger.info("PayTabs verified result: %s", result)

            order = Order.objects.filter(pk=int(result["cart_id"])).first()
            if order:
                status = result["payment_result"]["response_status"]
                if status == "A":
                    workspace_id = change_plan(
                        owner_email=order.owner_email,
                        workspace_id=order.workspace_id,
                        plan_id=order.plan.plan_id,
                    )
                    if not workspace_id:
                        # TODO error
                        return
                    order.workspace_id = workspace_id
                    order.status = "paid"
                else:
                    order.status = "failed"
                order.paytabs_transaction_id = tran_ref
                order.raw_response = result
                order.save()
        except Exception as e:
            result = {"error": str(e)}

    return render(
        request,
        "payments/return.html",
        {
            "payload": payload,
            "verify": result,
        },
    )


def cancel_subscription(request):
    if request.method == "POST":
        workspace_id = request.GET.get("workspaceID")
        owner_email = request.GET.get("ownerEmail")
        free_plan_id = Plan.objects.filter(plan_id="free")
        workspace_id = change_plan(
            owner_email=owner_email,
            workspace_id=workspace_id,
            plan_id=free_plan_id,
        )
        if not workspace_id:
            messages.error(request, "خطأ أثناء إلغاء الاشتراك")
        else:
            messages.success(request, "تم إلغاء اشتراكك والرجوع إلى الخطة المجانية")

    plans = requests.get(
        f"{settings.UCHAT_BASE_URL}/plans",
        headers={
            "Authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()

    if plans.get("status", False) == "ok":
        plans = plans["data"]

    for plan in plans:
        plan["price"] = int(
            Prices.objects.filter(usd_price=plan["price"]).first().iqd_price or 1000_000
        )

    current_workspace = requests.get(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}",
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()

    if current_workspace["status"] == "ok":
        current_workspace["plan"] = (
            current_workspace["plan"].replace("'", "").split(",")
        )
    else:
        current_workspace["plan"] = "free"

    return render(
        request,
        "payments/checkout.html",
        {
            "workspace_id": workspace_id,
            "owner_email": owner_email,
            "plans": plans,
            "current_workspace": current_workspace,
        },
    )
