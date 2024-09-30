from django.db import models
from django.db.models import Q, F


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    book_id = models.IntegerField()
    user_id = models.IntegerField()

    def __str__(self):
        return (
            f"Borrowing book {self.book_id} by user {self.user_id}, "
            f"borrow date: {self.borrow_date}, "
            f"expected return: {self.expected_return_date}, "
            f"actual return: {self.actual_return_date or 'not returned yet'}"
        )

    class Meta:
        verbose_name_plural = "borrowings"
        ordering = ["-borrow_date", "-expected_return_date", "-actual_return_date"]
        constraints = [
            # 1. Expected return date must be after the borrow date.
            models.CheckConstraint(
                condition=Q(expected_return_date__gt=F("borrow_date")),
                name="expected return date must be after the borrow date",
            ),
            # 2. Actual return date, if provided,
            # must be after or equal to the borrow date.
            models.CheckConstraint(
                condition=Q(actual_return_date__gte=F("borrow_date"))
                | Q(actual_return_date__isnull=True),
                name="actual return date must be after or "
                "equal to the borrow date or null",
            ),
        ]
