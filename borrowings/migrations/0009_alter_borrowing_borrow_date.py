# Generated by Django 5.1.1 on 2024-10-11 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "borrowings",
            "0008_remove_borrowing_actual_return_date_must_be_after_or_equal_to_the_borrow_date_or_null",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrowing",
            name="borrow_date",
            field=models.DateField(auto_now_add=True),
        ),
    ]
