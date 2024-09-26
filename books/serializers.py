from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "cover",
            "inventory",
            "daily_fee",
        )

    def validate_daily_fee(self, value):
        if value <= 0 or value >= 1000:
            raise serializers.ValidationError(
                f"{value} must be in range [0.01, 999.99]"
            )
        return value
