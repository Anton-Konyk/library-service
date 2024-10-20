from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from books.models import Book
from user.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True, default=None)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    def __str__(self):
        return f"{self.user.email} : {self.book.title}, "

    class Meta:
        verbose_name_plural = "borrowings"
        ordering = ["borrow_date", "expected_return_date", "actual_return_date"]
        constraints = [
            # 1. Expected return date must be after the borrow date.
            models.CheckConstraint(
                condition=Q(expected_return_date__gt=F("borrow_date")),
                name="expected return date must be after the borrow date",
            ),
        ]
