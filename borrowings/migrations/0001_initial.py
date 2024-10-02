# Generated by Django 5.1.1 on 2024-10-01 10:12

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("books", "0002_alter_book_inventory"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Borrowing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("borrow_date", models.DateField()),
                ("expected_return_date", models.DateField()),
                ("actual_return_date", models.DateField(blank=True, null=True)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="borrowings",
                        to="books.book",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="borrowings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "borrowings",
                "ordering": [
                    "-borrow_date",
                    "-expected_return_date",
                    "-actual_return_date",
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("expected_return_date__gt", models.F("borrow_date"))
                        ),
                        name="expected return date must be after the borrow date",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("actual_return_date__gte", models.F("borrow_date")),
                            ("actual_return_date__isnull", True),
                            _connector="OR",
                        ),
                        name="actual return date must be after or equal to the borrow date or null",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("actual_return_date__lte", datetime.date(2024, 10, 1)),
                            ("actual_return_date__isnull", True),
                            _connector="OR",
                        ),
                        name="actual return date must be before or equal to today's date or null",
                    ),
                ],
            },
        ),
    ]
