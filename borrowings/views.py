from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
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

FINE_MULTIPLIER = 2


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type={"type": "string", "items": {"type": "name"}},
                description="Filtering by active borrowings (still not returned - 1, "
                "already returned - 0) ex. ?is_active=1",
            ),
            OpenApiParameter(
                "user_id",
                type={"type": "integer", "items": {"type": "id"}},
                description="Filter by user id for admin users, so admin can see "
                "all users’ borrowings, if not specified, but if "
                "specified - only for concrete user ex. ?user_id=2",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of routes."""
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BorrowingListSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return super().get_serializer_class()

    @transaction.atomic()
    def perform_create(self, serializer):

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

            payment = create_payment(
                request=self.request,
                borrowing=borrowing,
                amount=amount,
                status_payment="G",
                type_payment="P",
            )

            serializer.context["payment"] = payment

            telegram_helper = TelegramHelper()
            message = (
                f"Book '{borrowing.book.title}' has borrowed by user {borrowing.user.email}.\n"
                f"Expected return date: {borrowing.expected_return_date}.\n"
                f"Your link for payment: {payment.session_url}"
            )
            telegram_helper.send_message(message)

        except Exception as e:
            raise ValueError(f"Error occurred while creating payment: {str(e)}")

    def create(self, request, *args, **kwargs):
        """
        Before creating borrowing - simply check the number of pending payments
        If at least one exists - forbid borrowing
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        queryset = self.queryset.filter(user=self.request.user).filter(
            Q(payments__status="G") | Q(payments__status="E")
        )

        if queryset.count() > 0:
            return Response(
                {
                    "massage": "You have at least one unpaid payment. "
                    "You can't borrow new book.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BorrowingReturnView(APIView):
    """Return book function"""

    serializer_class = BorrowingCreateSerializer

    @transaction.atomic
    def post(self, request, id):
        try:

            borrowing = get_object_or_404(Borrowing, id=id)
            if borrowing.actual_return_date is None:
                borrowing.actual_return_date = timezone.now().date()
                borrowing.book.inventory += 1
                borrowing.book.save()
                borrowing.save()

                if borrowing.actual_return_date > borrowing.expected_return_date:
                    fine_amount = borrowing.book.daily_fee * FINE_MULTIPLIER
                    amount = calculate_amount(
                        borrowing.actual_return_date,
                        borrowing.expected_return_date,
                        fine_amount,
                    )

                    payment = create_payment(
                        request=self.request,
                        borrowing=borrowing,
                        amount=amount,
                        status_payment="G",
                        type_payment="F",
                    )

                    return Response(
                        {
                            "user": borrowing.user.email,
                            "returned_book": borrowing.book.title,
                            "fine_payment": payment.money,
                            "url_for_payment": payment.session_url,
                        },
                        status=status.HTTP_200_OK,
                    )

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
        except Exception as e:
            raise ValueError(f"Error occurred while creating payment: {str(e)}")
