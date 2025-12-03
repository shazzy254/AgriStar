import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=HTTPBasicAuth(
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET
    ))
    return r.json().get("access_token")

def stk_push(phone, amount, account_reference="AgriStar Order"):
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        (settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
    ).decode()

    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": "https://britt-unlacerated-alpinely.ngrok-free.dev/mpesa/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": "Payment for AgriStar order",
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload, headers=headers
    )

    return response.json()

def release_escrow_to_farmer(farmer_phone, amount):
    """
    Releases escrowed funds to the farmer using B2C payment.
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "InitiatorName": "testapi",  # Sandbox initiator name
        "SecurityCredential": "YOUR_ENCODED_PASSWORD",  # Sandbox security credential
        "CommandID": "BusinessPayment",
        "Amount": amount,
        "PartyA": settings.MPESA_SHORTCODE,  # Your business shortcode
        "PartyB": farmer_phone,              # Farmer's phone number
        "Remarks": "AgriStar Escrow Release",
        "QueueTimeOutURL": "https://britt-unlacerated-alpinely.ngrok-free.dev/mpesa/b2c/timeout/",
        "ResultURL": "https://britt-unlacerated-alpinely.ngrok-free.dev/mpesa/b2c/result/"
    }

    # SIMULATION FOR DEMO:
    # If we don't have a real certificate/credential, return a success mock
    if payload["SecurityCredential"] == "YOUR_ENCODED_PASSWORD":
        return {
            "ConversationID": "AGRISTAR_DEMO_CONVERSATION_ID",
            "OriginatorConversationID": "AGRISTAR_DEMO_ORIGINATOR_ID",
            "ResponseCode": "0",
            "ResponseDescription": "Accept the service request successfully."
        }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest",
        json=payload, headers=headers
    )

    return response.json()