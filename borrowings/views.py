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
from helpers.telegram_helper import TelegramHelper


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
        if self.action == "list" or self.action == "retrieve":
            return BorrowingListSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        book.inventory -= 1
        book.save()
        borrowing = serializer.save(user=self.request.user)

        telegram_helper = TelegramHelper()
        message = (
            f"Book '{borrowing.book.title}' has borrowed by user {borrowing.user.email}.\n"
            f"Expected return date: {borrowing.expected_return_date}."
        )
        telegram_helper.send_message(message)


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
