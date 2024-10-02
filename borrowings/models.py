from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from books.models import Book
from user.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now=timezone.now().date())
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    def __str__(self):
        return f"{self.user.email} : {self.book.title}, "

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
            # 3. Actual return date, if provided,
            # must be before or equal to today's date.
            models.CheckConstraint(
                condition=Q(actual_return_date__lte=timezone.now().date())
                | Q(actual_return_date__isnull=True),
                name="actual return date must be before or "
                "equal to today's date or null",
            ),
        ]
