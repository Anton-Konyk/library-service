from django.urls import path, include
from rest_framework import routers

from borrowings.views import BorrowingViewSet, BorrowingReturnView
from payment.views import StripeSuccessView, StripeCancelView

router = routers.DefaultRouter()
router.register("borrowings", BorrowingViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("borrowings/<int:id>/return/", BorrowingReturnView.as_view(), name="return"),
    path("stripe/success/", StripeSuccessView.as_view(), name="stripe-success"),
    path("stripe/cancel/", StripeCancelView.as_view(), name="stripe-cancel"),
]

app_name = "borrowings"
