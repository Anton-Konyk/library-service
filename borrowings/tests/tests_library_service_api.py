from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

BOOK_LIST_URL = reverse("books:book-list")
BORROWING_LIST_URL = reverse("borrowings:borrowing-list")
PAYMENT_LIST_URL = reverse("payment:payment-list")


def sample_book(**params) -> Book:
    defaults = {
        "title": "Test Title",
        "author": "Test Author",
        "cover": "H",
        "inventory": 10,
        "daily_fee": 0.1,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedLibraryServiceApiTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_unauth_required_book(self):
        res = self.client.get(BOOK_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_auth_create_book(self):
        book_data = {
            "title": "Test Title",
            "author": "Test Author",
            "cover": "H",
            "inventory": 10,
            "daily_fee": 0.1,
        }
        res = self.client.post(BOOK_LIST_URL, book_data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauth_required_borrowing(self):
        res = self.client.get(BORROWING_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauth_required_payment(self):
        res = self.client.get(PAYMENT_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedLibraryServiceApiTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="test_password"
        )
        self.client.force_authenticate(self.user)  # logining test user
