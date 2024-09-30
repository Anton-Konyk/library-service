from rest_framework import viewsets

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingListSerializer

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return BorrowingListSerializer
        return super().get_serializer_class()
