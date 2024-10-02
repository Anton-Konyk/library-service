# Generated by Django 5.1.1 on 2024-10-01 18:06

import datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0004_alter_book_unique_together"),
        (
            "borrowings",
            "0003_remove_borrowing_actual_borrow_date_must_be_equal_to_today_s_date_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="borrowing",
            name="actual borrow date must be equal to today's date",
        ),
        migrations.AddConstraint(
            model_name="borrowing",
            constraint=models.CheckConstraint(
                condition=models.Q(("borrow_date__exact", datetime.date(2024, 10, 1))),
                name="actual borrow date must be equal to today's date",
            ),
        ),
    ]
