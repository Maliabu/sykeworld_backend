# payments/services.py

from django.db import transaction
from .models import Payment, PaymentLog
from bookings.models import Booking
from django.core.exceptions import ValidationError


class PaymentService:

    @staticmethod
    @transaction.atomic
    def create_payment(data):

        booking = Booking.objects.get(id=data["booking_id"])

        # Validate amount
        if data["amount"] != float(booking.total_price):
            raise ValidationError("Amount does not match booking total.")

        payment = Payment.objects.create(
            user=booking.user,
            booking=booking,
            amount=data["amount"],
            method=data["method"],
            reference=data.get("reference", "")
        )

        PaymentLog.objects.create(
            payment=payment,
            status="pending",
            message="Payment initiated"
        )

        return payment

    @staticmethod
    @transaction.atomic
    def confirm_payment(payment_id, transaction_id):

        payment = Payment.objects.get(id=payment_id)
        payment.status = "success"
        payment.transaction_id = transaction_id
        payment.save()

        PaymentLog.objects.create(
            payment=payment,
            status="success",
            message="Payment confirmed"
        )

        # Update booking status
        booking = payment.booking
        booking.status = "confirmed"
        booking.save()

        return payment

# pesapal_service.py

import requests
from django.conf import settings

def pesapal_get_token():
    url = f"{settings.PESAPAL_BASE_URL}/api/Auth/RequestToken"
    payload = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()

        if "token" not in data:
            raise Exception(data)

        return data["token"]

    except Exception as e:
        raise Exception(f"Pesapal token error: {str(e)}")


class PesapalAPI:
    def __init__(self):
        self.consumer_key = settings.PESAPAL_CONSUMER_KEY
        self.consumer_secret = settings.PESAPAL_CONSUMER_SECRET
        self.base_url = "https://pay.pesapal.com/v3"

        # placeholders (we fill these in next steps)
        self.token = None

    # Step 2 will fill this
    def authenticate(self):
        raise NotImplementedError("Authentication not implemented yet")

    # Step 3 will fill this
    def submit_order(self, order_data):
        raise NotImplementedError("Order submission not implemented yet")

    # Step 4 will fill this
    def get_payment_status(self, order_tracking_id):
        raise NotImplementedError("Payment status check not implemented yet")
