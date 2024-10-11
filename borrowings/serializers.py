from django.utils import timezone

from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.SlugRelatedField(read_only=True, many=False, slug_field="email")
    payment = serializers.StringRelatedField(
        many=True, read_only=True, source="payments"
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "payment",
            "user",
        )


class BorrowingListWithoutPaymentSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.SlugRelatedField(read_only=True, many=False, slug_field="email")

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    payment = serializers.StringRelatedField(
        many=True, read_only=True, source="payments"
    )
    url_payment = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
            "user",
            "payment",
            "url_payment",
        )

    def validate_book(self, value):
        if value.inventory == 0:
            raise serializers.ValidationError(
                "This book is not available for borrowing as inventory is 0."
            )
        return value

    def get_url_payment(self, obj):
        payment = obj.payments.first()
        if payment:
            return payment.session_url
        return None

    def validate_expected_return_date(self, expected_return_date):
        if expected_return_date <= timezone.now().date():
            raise serializers.ValidationError(
                "Expected return date must be after borrow date."
            )

        return expected_return_date
