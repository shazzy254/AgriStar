
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

def get_access_token():
    base_url = "https://api.safaricom.co.ke" if settings.MPESA_ENV == 'production' else "https://sandbox.safaricom.co.ke"
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    
    response = requests.get(url, auth=HTTPBasicAuth(
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET
    ))
    try:
        return response.json().get("access_token")
    except Exception as e:
        print("M-Pesa Access Token Error:", response.text)
        return None

# IMPORTANT: UPDATE THIS URL TO YOUR CURRENT RUNNING NGROK URL
# Example: "https://your-id.ngrok-free.app"
# Make sure to include "https://" and NO trailing slash
NGROK_URL = "https://britt-unlacerated-alpinely.ngrok-free.dev"

def stk_push(phone, amount, account_reference="AgriStar Order"):
    # Robust Phone Formatting
    phone = str(phone).strip().replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("7") or phone.startswith("1"):
        phone = "254" + phone
        
    access_token = get_access_token()
    if not access_token:
        print("M-Pesa Logic Error: Could not generate Access Token. Check Credentials.")
        return {"ResponseCode": "1", "ResponseDescription": "Failed to authenticate with M-Pesa."}
        
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
        "Amount": int(amount), # Ensure integer
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": f"{NGROK_URL}/mpesa/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": "Payment for AgriStar order",
    }

    base_url = "https://api.safaricom.co.ke" if settings.MPESA_ENV == 'production' else "https://sandbox.safaricom.co.ke"
    try:
        print(f"Sending STK Push to {phone} for KES {amount} (Env: {settings.MPESA_ENV})...")
        response = requests.post(
            f"{base_url}/mpesa/stkpush/v1/processrequest",
            json=payload, headers=headers
        )
        
        # Log to file
        with open("mpesa_debug.log", "a") as f:
            f.write(f"[{datetime.now()}] Phone: {phone}, Amount: {amount}, Response: {response.text}\n")
            
        print("M-Pesa API Response:", response.text)
        return response.json()
    except Exception as e:
        with open("mpesa_debug.log", "a") as f:
             f.write(f"[{datetime.now()}] Error: {str(e)}\n")
        print(f"M-Pesa Network Error: {e}")
        return {"ResponseCode": "1", "ResponseDescription": str(e)}

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
        "QueueTimeOutURL": f"{NGROK_URL}/mpesa/b2c/timeout/",
        "ResultURL": f"{NGROK_URL}/mpesa/b2c/result/"
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