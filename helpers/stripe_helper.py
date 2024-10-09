import os

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response

import stripe

from borrowings.models import Borrowing
from payment.models import Payment, STATUS_CHOICES, TYPE_CHOICES
from rest_framework.exceptions import APIException
from rest_framework import status


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# stripe.api_key = os.getenv("POSTGRES_HOST")


class StripePaymentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "There was an issue processing the payment with Stripe."
    default_code = "stripe_payment_error"


class CreateStripeSessionView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            borrowing_id = request.data.get("borrowing_id")
            payment_status = request.data.get("payment_status")
            payment_type = request.data.get("payment_type")
            amount = request.data.get("amount")
            quantity = int(request.data.get("quantity"))

            if payment_status not in dict(STATUS_CHOICES):
                return Response(
                    {"error": "Invalid status value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if payment_type not in dict(TYPE_CHOICES):
                return Response(
                    {"error": "Invalid type value"}, status=status.HTTP_400_BAD_REQUEST
                )

            borrowing = get_object_or_404(Borrowing, id=borrowing_id)

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Payment for the book borrowing",
                            },
                            "unit_amount": amount,
                        },
                        "quantity": quantity,
                    }
                ],
                mode="payment",
                success_url="http://localhost:8001/success",
                cancel_url="http://localhost:8001/cancel",
            )
            amount_total = int(amount) / 100
            payment = Payment.objects.create(
                status=payment_status,
                type=payment_type,
                borrowing=borrowing,
                session_url=session.url,
                session_id=session.id,
                money=amount_total,
            )
            print(f"Payment objects: {payment}")
            return Response(
                {"sessionId": session.id, "sessionUrl": session.url},
                status=status.HTTP_200_OK,
            )

        except stripe.error.CardError as e:
            raise ValidationError(
                {"detail": "Your card was declined. Please check the card details."}
            )

        except stripe.error.InvalidRequestError as e:
            raise ValidationError(
                {"detail": "Invalid parameters were supplied to Stripe's API."}
            )

        except stripe.error.AuthenticationError as e:
            raise StripePaymentException(
                "Authentication with Stripe failed. Please check your API keys."
            )

        except stripe.error.APIConnectionError as e:
            raise StripePaymentException("Network error: Unable to connect to Stripe.")

        except stripe.error.StripeError as e:
            raise StripePaymentException(
                "An error occurred while processing the payment. Please try again."
            )

        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    @staticmethod
    def create_payment(
        borrowing: Borrowing,
        amount: int,
        status_payment: str,
        type_payment: str,
        quantity: int = 1,
    ):
        request_data = {
            "borrowing_id": borrowing.id,
            "amount": amount,
            "payment_status": status_payment,
            "payment_type": type_payment,
            "quantity": quantity,
        }
        try:

            factory = APIRequestFactory()
            request = factory.post(reverse("create-stripe-session"), data=request_data)

            view = CreateStripeSessionView.as_view()
            response = view(request)

            if response.status_code == 200:
                borrowing.payment_session_url = response.data["sessionUrl"]
                borrowing.payment_session_id = response.data["sessionId"]
                borrowing.save()

        except StripePaymentException as e:
            raise StripePaymentException(f"Payment failed: {str(e)}")

        except Exception as e:
            raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})
