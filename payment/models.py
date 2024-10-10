from django.db import models

from borrowings.models import Borrowing


STATUS_CHOICES = (
    ("G", "PENDING"),
    ("D", "PAID"),
)

TYPE_CHOICES = (
    ("P", "PAYMENT"),
    ("F", "FINE"),
)


class Payment(models.Model):
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="G")
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default="P")
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255)
    money = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.borrowing.id} {self.status} {self.type} {self.money}"

    class Meta:
        verbose_name_plural = "payments"
        ordering = [
            "money",
        ]
