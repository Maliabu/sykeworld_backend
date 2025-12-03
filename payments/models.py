# payments/models.py

from django.db import models
from django.contrib.auth.models import User
from accounts.models import CustomUser
from bookings.models import Booking
from django.conf import settings


PAYMENT_METHODS = (
    ("card", "Card Payment"),
    ("bank", "Bank Transfer"),
    ("cash", "Cash at Hotel"),
)


PAYMENT_STATUS = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("success", "Success"),
    ("failed", "Failed"),
    ("refunded", "Refunded"),
)


class Payment(models.Model):
    booking = models.ForeignKey(
        Booking,   # lazy reference OK
        on_delete=models.CASCADE,
        related_name="payments"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # correct reference to custom user
        on_delete=models.CASCADE,
        related_name="payments"
    )

    pesapal_order_tracking_id = models.CharField(max_length=255, blank=True, null=True)
    pesapal_merchant_reference = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="PENDING")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"


class PaymentLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for Payment #{self.payment.id}"

class Transaction(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="transactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    pesapal_reference = models.CharField(max_length=200, unique=True)
    merchant_reference = models.CharField(max_length=200)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="PENDING")  
    payment_method = models.CharField(max_length=50, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.booking} — {self.status}"