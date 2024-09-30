# Generated by Django 5.1.1 on 2024-09-30 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

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
                ("book_id", models.IntegerField()),
                ("user_id", models.IntegerField()),
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
                ],
            },
        ),
    ]
