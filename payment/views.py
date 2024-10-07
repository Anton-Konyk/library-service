from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from payment.models import Payment
from payment.serializers import PaymentListSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in ["list", "retrieve"] and not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)
            return queryset

        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PaymentListSerializer
        return super().get_serializer_class()
