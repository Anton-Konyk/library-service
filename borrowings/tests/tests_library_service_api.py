import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingListSerializer

BOOK_LIST_URL = reverse("books:book-list")
BORROWING_LIST_URL = reverse("borrowings:borrowing-list")
PAYMENT_LIST_URL = reverse("payment:payment-list")
BORROWING_DAYS = 3


def sample_book(**params) -> Book:
    defaults = {
        "title": "Test Title",
        "author": "Test Author",
        "cover": "H",
        "inventory": 10,
        "daily_fee": 1,
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
            "daily_fee": 1,
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

        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="admin_password",
        )

    def test_auth_create_book(self):
        book_data = {
            "title": "Test Title",
            "author": "Test Author",
            "cover": "H",
            "inventory": 10,
            "daily_fee": 1,
        }
        self.client.force_authenticate(self.user)
        res = self.client.post(BOOK_LIST_URL, book_data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_create_book(self):
        book_data = {
            "title": "Test Title",
            "author": "Test Author",
            "cover": "H",
            "inventory": 10,
            "daily_fee": 1,
        }
        self.client.force_authenticate(self.admin_user)
        res = self.client.post(BOOK_LIST_URL, book_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_auth_required_borrowings(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_borrowing_id = res.data["id"]
        borrowing_ids = [borrowing["id"] for borrowing in serializer.data]
        self.assertIn(created_borrowing_id, borrowing_ids)

    def test_auth_borrowing_date_equal_current_day(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today(),
            "book": book.id,
            "user": self.user.id,
        }
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Expected return date must be after borrow date.",
            res.data["expected_return_date"],
        )

    def test_auth_borrowing_date_less_current_day(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() - datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Expected return date must be after borrow date.",
            res.data["expected_return_date"],
        )

    def test_auth_borrowing_inventory(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        book_inventory_before_borrowing = book.inventory
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        book_inventory_after_borrowing = Book.objects.get(id=res.data["book"]).inventory
        self.assertEqual(
            book_inventory_after_borrowing, book_inventory_before_borrowing - 1
        )

    def test_auth_prohibited_borrowing_inventory_zero(self):
        self.client.force_authenticate(self.user)
        book = Book.objects.create(
            title="Test Title",
            author="Test Author",
            cover="H",
            inventory=0,
            daily_fee=1,
        )
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "This book is not available for borrowing as inventory is 0.",
            res.data["book"],
        )

    def test_auth_check_amount_borrowing(self):
        self.client.force_authenticate(self.user)
        book = Book.objects.create(
            title="Test Title",
            author="Test Author",
            cover="H",
            inventory=10,
            daily_fee=1.2,
        )
        borrow_data = {
            "expected_return_date": datetime.date.today()
            + datetime.timedelta(days=BORROWING_DAYS),
            "book": book.id,
            "user": self.user.id,
        }
        payment_amount = Decimal(book.daily_fee * BORROWING_DAYS).quantize(
            Decimal("0.01")
        )
        res = self.client.post(BORROWING_LIST_URL, borrow_data)
        result = Decimal(res.data["payment"][0].split()[3]).quantize(Decimal("0.01"))
        self.assertEqual(result, payment_amount)

    def test_auth_list_borrowings(self):
        book = sample_book()

        self.client.force_authenticate(self.admin_user)
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res_admin = self.client.post(BORROWING_LIST_URL, borrow_data)

        self.client.force_authenticate(self.user)
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=2),
            "book": book.id,
            "user": self.user.id,
        }
        res_user = self.client.post(BORROWING_LIST_URL, borrow_data)
        res_list_user = self.client.get(BORROWING_LIST_URL)
        self.assertEqual(len(res_list_user.data), 1)
        self.assertEqual(res_list_user.data[0]["user"], self.user.email)

    def test_admin_list_borrowings(self):

        self.client.force_authenticate(self.user)
        book_user = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book_user.id,
            "user": self.user.id,
        }
        res_user = self.client.post(BORROWING_LIST_URL, borrow_data)
        res_list_user = self.client.get(BORROWING_LIST_URL)

        self.client.force_authenticate(self.admin_user)
        book_admin = sample_book(title="Test Title Admin", daily_fee=2)
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=2),
            "book": book_admin.id,
            "user": self.user.id,
        }
        res_admin = self.client.post(BORROWING_LIST_URL, borrow_data)
        res_list_admin = self.client.get(BORROWING_LIST_URL)

        self.assertIn(res_list_user.data[0], res_list_admin.data)

    def test_return_borrowing_book(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res_borrowing_user = self.client.post(BORROWING_LIST_URL, borrow_data)
        borrowing_id = res_borrowing_user.data["id"]
        book_id = res_borrowing_user.data["book"]
        book_title = Book.objects.get(id=book_id).title
        borrowing_return_url = reverse("borrowings:return", args=[borrowing_id])
        res_return_user = self.client.post(borrowing_return_url)

        self.assertEqual(
            res_return_user.data["detail"],
            f"User {self.user.email} have " f"returned book {book_title} successfully.",
        )

    def test_return_borrowing_inventory(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res_borrowing_user = self.client.post(BORROWING_LIST_URL, borrow_data)
        book_id = res_borrowing_user.data["book"]
        inventory_book_when_borrowing = Book.objects.get(id=book_id).inventory
        borrowing_id = res_borrowing_user.data["id"]

        borrowing_return_url = reverse("borrowings:return", args=[borrowing_id])
        res_return_user = self.client.post(borrowing_return_url)

        inventory_after_borrow = Book.objects.get(id=book_id).inventory
        self.assertEqual(inventory_book_when_borrowing + 1, inventory_after_borrow)

    def test_impossible_twice_return_borrowing_book(self):
        self.client.force_authenticate(self.user)
        book = sample_book()
        borrow_data = {
            "expected_return_date": datetime.date.today() + datetime.timedelta(days=1),
            "book": book.id,
            "user": self.user.id,
        }
        res_borrowing_user = self.client.post(BORROWING_LIST_URL, borrow_data)
        borrowing_id = res_borrowing_user.data["id"]
        borrowing_return_url = reverse("borrowings:return", args=[borrowing_id])
        res_return_user = self.client.post(borrowing_return_url)
        borrowing_return_url = reverse("borrowings:return", args=[borrowing_id])
        res_second_return_user = self.client.post(borrowing_return_url)
        self.assertEqual(
            res_second_return_user.data["detail"],
            f"User {self.user.email} already have returned book "
            f"Test Title on {datetime.date.today()}",
        )
