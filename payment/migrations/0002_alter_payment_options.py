# Generated by Django 5.1.1 on 2024-10-08 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="payment",
            options={"ordering": ["money"], "verbose_name_plural": "payments"},
        ),
    ]
