# payments/utils.py
import requests
from django.conf import settings

def get_pesapal_access_token():
    url = "https://pay.pesapal.com/v3/api/Auth/RequestToken"

    payload = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }

    res = requests.post(url, json=payload)
    res.raise_for_status()

    return res.json()["token"]


def verify_pesapal_transaction(order_tracking_id: str):
    """
    Calls Pesapal API to verify a transaction.
    Returns a dict: { 'status': 'COMPLETED' / 'FAILED' / 'PENDING', ... }
    """

    token = get_pesapal_access_token()

    url = f"{settings.PESAPAL_API_URL}/api/Transactions/GetTransactionStatus"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "orderTrackingId": order_tracking_id
    }

    r = requests.post(url, json=payload, headers=headers)

    try:
        data = r.json()
    except Exception:
        return {"status": "ERROR", "raw": r.text}

    # Pesapal response structure:
    # {
    #   "payment_status_description": "Completed",
    #   "status_code": "000",
    #   "status": "COMPLETED",
    #   ...
    # }

    return {
        "status": data.get("status"),
        "data": data
    }