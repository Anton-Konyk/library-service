from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingCreateSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list" and not self.request.user.is_staff:
            queryset = self.queryset.filter(user=self.request.user)
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
        serializer.save(user=self.request.user)
