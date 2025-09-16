from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Plan, Order
from .utils.paytabs import create_pay_page

import logging

logger = logging.getLogger("payments")


def plans_list(request):
    plans = Plan.objects.all()
    return render(request, "payments/plans.html", {"plans": plans})


def subscribe(request, plan_slug):
    plan = get_object_or_404(Plan, slug=plan_slug)
    order = Order.objects.create(plan=plan, amount=plan.price, currency=plan.currency)

    customer = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "0000000000",
    }

    data = create_pay_page(order, customer)
    order.raw_response = data
    order.save()

    redirect_url = (
        data.get("redirect_url") or data.get("payment_url") or data.get("payment_link")
    )
    if redirect_url:
        return redirect(redirect_url)
    return HttpResponse("Error creating payment session")


from .utils.paytabs import create_pay_page, verify_transaction


@csrf_exempt
def paytabs_return(request):
    payload = request.POST.dict() if request.method == "POST" else request.GET.dict()
    tran_ref = payload.get("tran_ref") or payload.get("transaction_id")

    order = None
    result = None
    if tran_ref:
        try:
            result = verify_transaction(tran_ref)

            logger.info("PayTabs return payload: %s", payload)
            if result:
                logger.info("PayTabs verified result: %s", result)

            # استخرج الـ order_id من custom_payment_name لو موجود
            custom = result.get("custom_payment_name") or ""
            if custom.startswith("UChat-"):
                order_id = int(custom.split("-")[1])
                order = Order.objects.filter(pk=order_id).first()
                if order:
                    status = result.get("response_status") or result.get(
                        "payment_result", {}
                    ).get("response_status")
                    if status in ("A", "captured", "Paid", "CAPTURED"):
                        order.status = "paid"
                    else:
                        order.status = "failed"
                    order.paytabs_transaction_id = tran_ref
                    order.raw_response = result
                    order.save()
        except Exception as e:
            result = {"error": str(e)}

    return render(
        request, "payments/return.html", {"payload": payload, "verify": result}
    )


@csrf_exempt
def paytabs_webhook(request):
    """
    PayTabs server-to-server notification (IPN/webhook).
    بعد استلام أي إشعار، نعمل verify من PayTabs API ونحدث الـ Order.
    """
    payload = request.POST.dict() if request.method == "POST" else request.GET.dict()
    tran_ref = payload.get("tran_ref") or payload.get("transaction_id")

    result = None
    order = None

    if tran_ref:
        try:
            # نتحقق من المعاملة
            result = verify_transaction(tran_ref)

            logger.info("PayTabs webhook payload: %s", payload)
            if result:
                logger.info("PayTabs verified result: %s", result)

            # نجيب الـ order_id من custom_payment_name اللي بعتناه وقت الإنشاء
            custom = result.get("custom_payment_name") or ""
            if custom.startswith("UChat-"):
                order_id = int(custom.split("-")[1])
                order = Order.objects.filter(pk=order_id).first()

            if order:
                status = result.get("response_status") or result.get(
                    "payment_result", {}
                ).get("response_status")
                if status in ("A", "captured", "Paid", "CAPTURED"):
                    order.status = "paid"
                else:
                    order.status = "failed"
                order.paytabs_transaction_id = tran_ref
                order.raw_response = result
                order.save()

        except Exception as e:
            result = {"error": str(e)}

    # نرجع 200 OK عشان PayTabs يعتبر إننا استقبلنا الإشعار
    return HttpResponse("OK")
