from datetime import timedelta

from celery import shared_task
from django.db.models import Q

from django.utils import timezone

from borrowings.models import Borrowing
from helpers.telegram_helper import TelegramHelper


@shared_task
def borrowing_notification() -> None:
    """
    The function filters all borrowings, which are overdue
    (expected_return_date is tomorrow or less, and the book
    is still not returned) and send a notification to the
    telegram chat about each overdue separately with
    detailed information.
    If no borrowings are overdue for that day -
    send a “No borrowings overdue today!” notification.
    """
    tomorrow = timezone.now().date() + timedelta(days=1)
    queryset = Borrowing.objects.filter(
        Q(expected_return_date__lte=tomorrow) & Q(actual_return_date__isnull=True)
    )
    if queryset.exists():
        for borrowing in queryset:
            telegram_helper = TelegramHelper()
            message = (
                f"Dear {borrowing.user.email} your day for return book '{borrowing.book.title}' "
                f"is {borrowing.expected_return_date}.\n"
                f"Please make it ontime!"
            )
            telegram_helper.send_message(message)
    else:
        telegram_helper = TelegramHelper()
        message = f"“No borrowings overdue today!”"
        telegram_helper.send_message(message)
