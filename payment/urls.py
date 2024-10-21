from django.urls import path, include
from rest_framework import routers

from payment.views import PaymentViewSet, RenewPaymentSessionView

router = routers.DefaultRouter()
router.register("payment", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("payment/<int:id>/renew/", RenewPaymentSessionView().as_view(), name="renew"),
]

app_name = "payment"
