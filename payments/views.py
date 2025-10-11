from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.urls import reverse


from .models import Plan, Order, Prices
from .utils.paytabs import create_pay_page, verify_transaction
from .utils.uchat import change_plan

import json
import requests
import logging

logger = logging.getLogger("payments")


def checkout(request):
    workspace_id = request.GET.get("workspaceID")
    owner_email = request.GET.get("ownerEmail")

    if not owner_email or not workspace_id:
        return render(request, "payments/missing_info.html")

    plans = requests.get(
        f"{settings.UCHAT_BASE_URL}/plans",
        headers={
            "Authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()

    if plans.get("status", False) == "ok":
        plans = plans["data"]

    for plan in plans:
        plan_price = Prices.objects.filter(usd_price=plan["price"]).first()
        plan["price"] = int(plan_price.iqd_price) if plan_price else 1000_000
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

    if not owner_email or not workspace_id:
        return render(request, "payments/missing_info.html")
    
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
        if workspace_id:
            order.workspace_id = workspace_id
            order.status = "paid"
        else:
            order.status = "error"
        order.save()
        return render(
            request,
            "payments/success.html",
            {
                "workspace_id": workspace_id,
                "owner_email": owner_email,
                "plan": plan,
            },
        )

    data = create_pay_page(order)
    order.raw_response = data
    order.save()

    redirect_url = (
        data.get("redirect_url") or data.get("payment_url") or data.get("payment_link")
    )
    if redirect_url:
        logger.info("Redirecting to pay page for order: %s", order.id)
        return redirect(redirect_url)

    return HttpResponse("Error creating payment session")


@csrf_exempt
def paytabs_callback(request):
    try:
        # Parse JSON body (PayTabs sends JSON, not form-encoded)
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST.dict() or request.GET.dict()

    tran_ref = payload.get("tran_ref") or payload.get("tranRef")

    logger.info("PayTabs callback payload: %s", payload)

    if not tran_ref:
        return JsonResponse({"error": "Missing tran_ref"}, status=400)

    result = verify_transaction(tran_ref)
    logger.info("PayTabs verified result: %s", result)

    order = Order.objects.filter(pk=int(result["cart_id"])).first()
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)

    status = result["payment_result"]["response_status"]
    if status == "A":  # Approved
        workspace_id = change_plan(
            owner_email=order.owner_email,
            workspace_id=order.workspace_id,
            plan_id=order.plan.plan_id,
        )
        if workspace_id:
            order.workspace_id = workspace_id
            order.status = "paid"
        else:
            order.status = "error"
    else:
        order.status = "failed"

    order.paytabs_transaction_id = tran_ref
    order.raw_response = result
    order.save()

    return JsonResponse({"status": "ok"})


@csrf_exempt
def paytabs_return(request):
    try:
        # Parse JSON body (PayTabs sends JSON, not form-encoded)
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST.dict() or request.GET.dict()

    tran_ref = payload.get("tran_ref") or payload.get("tranRef")

    if not tran_ref:
        return JsonResponse({"error": "Missing tran_ref"}, status=400)

    result = verify_transaction(tran_ref)

    order = Order.objects.filter(pk=int(result["cart_id"])).first()
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)

    return render(
        request,
        "payments/return.html",
        {
            "workspace_id": order.workspace_id,
            "owner_email": order.owner_email,
            "payload": payload,
            "verify": result,
        },
    )


def cancel_subscription(request):
    if request.method == "POST":
        owner_email = request.POST.get("ownerEmail")
        workspace_id = request.POST.get("workspaceID")

        if not owner_email or not workspace_id:
            return render(request, "payments/missing_info.html")

        success = change_plan(
            owner_email=owner_email,
            workspace_id=workspace_id,
            plan_id="free",
        )

        if not success:
            messages.error(request, "خطأ أثناء إلغاء الاشتراك")
        else:
            messages.success(request, "تم إلغاء اشتراكك والرجوع إلى الخطة المجانية")

        # ✅ redirect back to checkout with original params
        checkout_url = (
            reverse("payments:plans")
            + f"?workspaceID={workspace_id}&ownerEmail={owner_email}"
        )
        return redirect(checkout_url)
    
    # fallback for GET or bad request
    messages.error(request, "طلب غير صالح")
    return HttpResponse("Bad Request")
