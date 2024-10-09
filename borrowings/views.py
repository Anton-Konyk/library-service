from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingCreateSerializer,
)
from helpers.stripe_helper import create_payment
from helpers.telegram_helper import TelegramHelper


def calculate_amount(last_day: date, first_day: date, rate: Decimal) -> int:

    if not isinstance(last_day, date) or not isinstance(first_day, date):
        raise ValueError("last_day and first_day must have type date.")

    if rate < Decimal("0.00"):
        raise ValueError("rate must be positive.")

    delta_days = (last_day - first_day).days

    if delta_days < 0:
        raise ValueError("last_day must be later first_day.")

    amount = Decimal(delta_days) * rate

    return int((amount * 100).quantize(Decimal("0")))


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()

        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        filters = Q()
        if is_active:
            if is_active == "1":
                filters &= Q(actual_return_date__isnull=True)
            else:
                filters &= ~Q(actual_return_date__isnull=True)
        if user_id:
            filters &= Q(user__id=user_id)

        queryset = queryset.filter(filters)

        if self.action == "list" and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            return queryset

        if self.action == "retrieve" and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            return queryset

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BorrowingListSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):

        with transaction.atomic():
            try:

                book = serializer.validated_data["book"]

                book.inventory -= 1
                book.save()
                borrowing = serializer.save(user=self.request.user)
                amount = calculate_amount(
                    borrowing.expected_return_date,
                    borrowing.borrow_date,
                    borrowing.book.daily_fee,
                )
                # stripe_helper = CreateStripeSessionView()
                create_payment(
                    borrowing, amount=amount, status_payment="G", type_payment="P"
                )

                telegram_helper = TelegramHelper()
                message = (
                    f"Book '{borrowing.book.title}' has borrowed by user {borrowing.user.email}.\n"
                    f"Expected return date: {borrowing.expected_return_date}."
                )
                telegram_helper.send_message(message)

            except Exception as e:
                transaction.set_rollback(True)

                raise ValueError(f"Error occurred while creating payment: {str(e)}")


class BorrowingReturnView(APIView):
    """Return book function"""

    serializer_class = BorrowingCreateSerializer

    def post(self, request, id):
        borrowing = get_object_or_404(Borrowing, id=id)
        if borrowing.actual_return_date is None:
            borrowing.actual_return_date = timezone.now().date()
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            telegram_helper = TelegramHelper()
            message = f"Book '{borrowing.book.title}' has returned by user {borrowing.user.email}."
            telegram_helper.send_message(message)

            return Response(
                {
                    "detail": f"User {borrowing.user.email} have "
                    f"returned book {borrowing.book.title} successfully."
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "detail": f"User {borrowing.user.email} "
                    f"already have returned book {borrowing.book.title} "
                    f"on {borrowing.actual_return_date}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
