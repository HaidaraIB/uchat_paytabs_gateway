from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("", views.checkout, name="plans"),
    path("subscribe/<str:plan_id>", views.subscribe, name="subscribe"),
    path("payment_return", views.paytabs_return, name="paytabs_return"),
    path("payment_callback", views.paytabs_callback, name="paytabs_callback"),
    path("cancel_subscription", views.cancel_subscription, name="cancel_subscription"),
]
