import os

from django.core.exceptions import ValidationError

import stripe

from borrowings.models import Borrowing
from payment.models import Payment, STATUS_CHOICES, TYPE_CHOICES
from rest_framework.exceptions import APIException
from rest_framework import status


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class StripePaymentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "There was an issue processing the payment with Stripe."
    default_code = "stripe_payment_error"


def create_stripe_session(amount, quantity=1):
    try:
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
        return session

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


def create_payment(
    borrowing: Borrowing,
    amount: int,
    status_payment: str,
    type_payment: str,
    quantity: int = 1,
):

    try:
        session = create_stripe_session(amount, quantity)
        if status_payment not in dict(STATUS_CHOICES):
            raise ValueError(
                f"Invalid status value: {status_payment}."
                f"Must be one of {list(STATUS_CHOICES)}"
            )
        if type_payment not in dict(TYPE_CHOICES):
            raise ValueError(
                f"Invalid type value: {type_payment}."
                f"Must be one of {list(TYPE_CHOICES)}"
            )

        borrowing.payment_session_url = session.url
        borrowing.payment_session_id = session.id
        borrowing.save()

        payment = Payment.objects.create(
            status=status_payment,
            type=type_payment,
            borrowing=borrowing,
            session_url=session.url,
            session_id=session.id,
            money=amount / 100,
        )
        print(f"Payment objects: {payment}")

    except StripePaymentException as e:
        raise StripePaymentException(f"Payment failed: {str(e)}")

    except Exception as e:
        raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})
