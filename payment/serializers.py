from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer
from payment.models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing = BorrowingListSerializer(read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)
    type = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money",
        )

    def validate_money(self, value):
        if value <= 0 or value >= 1000000:
            raise serializers.ValidationError(
                f"{value} must be in range [0.01, 999999.99]"
            )
        return value
