# payments/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from payments.utils import verify_pesapal_transaction
from payments.utils import get_pesapal_access_token
from .services import PaymentService, pesapal_get_token
from .models import Payment, Transaction
import uuid, base64, hmac, hashlib, requests, json
from urllib.parse import urlencode
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Booking
from django.shortcuts import get_object_or_404


class PesapalTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            token = pesapal_get_token()
            return Response({"token": token}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@csrf_exempt
def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    try:
        payment = PaymentService.create_payment(data)
        return JsonResponse({
            "message": "Payment initiated",
            "payment_id": payment.id,
            "status": payment.status
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def confirm_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    payment_id = data.get("payment_id")
    transaction_id = data.get("transaction_id")

    payment = PaymentService.confirm_payment(payment_id, transaction_id)

    return JsonResponse({
        "message": "Payment confirmed",
        "payment_id": payment.id,
        "status": payment.status
    })


def list_payments(request, user_id):
    payments = Payment.objects.filter(user_id=user_id).values(
        "id", "amount", "status", "method", "booking_id"
    )
    return JsonResponse(list(payments), safe=False)


def generate_merchant_reference():
    return str(uuid.uuid4())

class PesapalInitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            booking_id = request.data.get("booking_id")
            amount = request.data.get("amount")
            user_id = request.data.get("user_id")

            if not booking_id or not amount or not user_id:
                return Response({"error": "Missing required fields"}, status=400)

            # 1. Get Pesapal access token
            token_url = "https://pay.pesapal.com/v3/api/Auth/RequestToken"
            token_payload = {
                "consumer_key": settings.PESAPAL_CONSUMER_KEY,
                "consumer_secret": settings.PESAPAL_CONSUMER_SECRET,
            }

            token_res = requests.post(token_url, json=token_payload)
            token_data = token_res.json()
            access_token = token_data["token"]

            # 2. Register order
            order_url = "https://pay.pesapal.com/v3/api/Transactions/SubmitOrderRequest"
            order_payload = {
                "id": booking_id,
                "currency": "UGX",
                "amount": amount,
                "description": "Room Booking Payment",
                "callback_url": settings.PESAPAL_CALLBACK_URL,
                "notification_id": settings.PESAPAL_NOTIFICATION_ID,
                "billing_address": {
                    "email_address": request.user.email if request.user.is_authenticated else "",
                    "phone_number": "",
                    "country_code": "UG",
                    "first_name": "",
                    "last_name": "",
                }
            }

            headers = {"Authorization": f"Bearer {access_token}"}

            order_res = requests.post(order_url, json=order_payload, headers=headers)
            order_data = order_res.json()

            redirect_url = order_data["redirect_url"]
            tracking_id = order_data["order_tracking_id"]

            # 3. Save payment record
            Payment.objects.create(
                booking_id=booking_id,
                user_id=user_id,
                amount=amount,
                pesapal_tracking_id=tracking_id
            )

            return Response({
                "redirect_url": redirect_url,
                "tracking_id": tracking_id,
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class PesapalCallbackView(APIView):
    permission_classes = []  # Pesapal servers do not send JWT

    def get(self, request):
        tracking_id = request.GET.get("OrderTrackingId")
        merchant_ref = request.GET.get("OrderMerchantReference")

        if not tracking_id or not merchant_ref:
            return Response({"error": "Missing parameters"}, status=400)

        # 1️⃣ Fetch the Payment record
        payment = get_object_or_404(Payment, id=merchant_ref)

        # 2️⃣ Get fresh access token
        token = get_pesapal_access_token()

        # 3️⃣ Confirm payment from Pesapal API
        url = f"{settings.PESAPAL_HOST}/api/Transactions/GetTransactionStatus"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"orderTrackingId": tracking_id}

        pesapal_res = requests.post(url, json=payload, headers=headers).json()

        status = pesapal_res.get("status")

        # 4️⃣ Update payment record
        payment.pesapal_transaction_tracking_id = tracking_id
        payment.status = status
        payment.save()

        # 5️⃣ If completed → mark booking as paid
        if status == "COMPLETED":
            booking = payment.booking
            booking.payment_status = "PAID"   # or booking.is_paid = True
            booking.save()

        return Response({"message": "Callback received"}, status=200)

class PesapalIPNCallback(APIView):
    permission_classes = []   # Pesapal does not send JWT
    authentication_classes = [] 

    def get(self, request):
        tracking_id = request.GET.get("OrderTrackingId")
        reference = request.GET.get("OrderReference")

        if not tracking_id or not reference:
            return Response({"error": "Missing fields"}, status=400)

        # Fetch transaction
        try:
            tx = Transaction.objects.get(tracking_id=tracking_id, reference=reference)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        # 1. Get Access Token again
        token_url = "https://pay.pesapal.com/v3/api/Auth/RequestToken"
        token_res = requests.post(
            token_url, 
            json={"consumer_key": settings.PESAPAL_CONSUMER_KEY,
                  "consumer_secret": settings.PESAPAL_CONSUMER_SECRET}
        )
        access_token = token_res.json().get("token")

        # 2. Hit Pesapal status API
        status_url = f"https://pay.pesapal.com/v3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
        status_res = requests.get(status_url, headers={"Authorization": f"Bearer {access_token}"})
        data = status_res.json()

        tx.status = data.get("payment_status_description", "UNKNOWN")
        tx.meta = data
        tx.save()

        # 3. If completed → mark booking as paid + create payment record
        if data.get("status") == "COMPLETED":
            booking = tx.booking
            booking.is_paid = True
            booking.save()

            # Make sure we do not double–create payments
            if not Payment.objects.filter(transaction=tx).exists():
                Payment.objects.create(
                    user=booking.user,
                    booking=booking,
                    transaction=tx,
                    amount=data.get("amount", booking.amount),
                    status="COMPLETED",
                )

        return Response({"message": "IPN received"}, status=200)


class PesapalIPNCallback(APIView):
    permission_classes = [AllowAny]   # Pesapal servers need access

    def post(self, request):
        """
        Pesapal sends: 
        {
            "OrderTrackingId": "",
            "OrderMerchantReference": ""
        }
        """
        print("IPN received:", request.data)

        merchant_ref = request.data.get("OrderMerchantReference")
        tracking_id = request.data.get("OrderTrackingId")

        if not merchant_ref or not tracking_id:
            return Response(
                {"error": "Missing merchant reference or tracking ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1️⃣ Fetch payment
        payment = get_object_or_404(Payment, id=merchant_ref)

        # 2️⃣ Get new token
        try:
            token = get_pesapal_access_token()
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # 3️⃣ Verify the transaction
        try:
            status_data = verify_pesapal_transaction(token, tracking_id)
        except Exception as e:
            return Response({"error": "Verification failed", "details": str(e)}, status=500)

        status_code = status_data.get("status")

        # 4️⃣ Update payment record
        payment.status = status_code
        payment.tracking_id = tracking_id
        payment.save()

        # 5️⃣ If PAID → mark booking as confirmed
        if status_code == "COMPLETED":
            booking = payment.booking
            booking.is_paid = True
            booking.save()

        return Response({"message": "IPN processed", "status": status_code})