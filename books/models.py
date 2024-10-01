from django.db import models


class Book(models.Model):

    STATUS_CHOICES = (
        ("H", "Hard"),
        ("S", "Soft"),
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=1, choices=STATUS_CHOICES, default="H")
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.author} " f"{self.title[0:10]}"

    class Meta:
        verbose_name_plural = "books"
        ordering = ["author", "title"]
