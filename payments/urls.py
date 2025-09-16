from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("", views.plans_list, name="plans"),
    path("subscribe/<slug:plan_slug>/", views.subscribe, name="subscribe"),
    path("paytabs_return/", views.paytabs_return, name="paytabs_return"),
    path("paytabs_webhook/", views.paytabs_webhook, name="paytabs_webhook"),
]
