from django.urls import path, include
from rest_framework import routers

from borrowings.views import BorrowingViewSet, BorrowingReturnView

router = routers.DefaultRouter()
router.register("borrowings", BorrowingViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("borrowings/<int:id>/return/", BorrowingReturnView.as_view(), name="return"),
]

app_name = "borrowings"
