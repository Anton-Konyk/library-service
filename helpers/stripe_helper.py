import os

from django.http import HttpRequest
from django.urls import reverse
from rest_framework.response import Response
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


def create_stripe_session(request, amount, quantity=1, currency="usd"):

    success_url = (
        request.build_absolute_uri(reverse("borrowings:stripe-success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = (
        request.build_absolute_uri(reverse("borrowings:stripe-cancel"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": "Payment for the book borrowing",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": quantity,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
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
    request: HttpRequest,
    borrowing: Borrowing,
    amount: int,
    status_payment: str,
    type_payment: str,
    quantity: int = 1,
):

    try:
        session = create_stripe_session(request, amount, quantity)
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
        return payment

    except StripePaymentException as e:
        raise StripePaymentException(f"Payment failed: {str(e)}")

    except Exception as e:
        raise ValidationError({"detail": f"An unexpected error occurred: {str(e)}"})


def stripe_success_check(payment: Payment):

    try:
        session = stripe.checkout.Session.retrieve(payment.session_id)

        if session.payment_status == "paid":
            payment.status = "D"
            payment.save()

            return Response(
                {"message": "Payment was successful."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Payment was not successful."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except stripe.error.StripeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
