import stripe
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class StripeSuccessView(APIView):
    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get("session_id")
        return Response(
            {"message": "Payment was successful!", "session_id": session_id},
            status=status.HTTP_200_OK,
        )


class StripeCancelView(APIView):
    def get(self, request):

        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            payment = Payment.objects.get(session_id=session_id)
            if payment.status == "G" and session.status == "open":
                return Response(
                    {
                        "message": "Payment session is available for 24 hours. You can complete the payment later.",
                        "payment_status": payment.status,
                        "your_payment_session_url": payment.session_url,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "message": "Payment session is not available or already completed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
