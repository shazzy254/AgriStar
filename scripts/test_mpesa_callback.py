
import os
import sys
import django
import json
import requests

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AgriStar.settings")
django.setup()

from marketplace.models import Order

def run():
    # Find an order to test
    order = Order.objects.filter(status='ACCEPTED').last()
    if not order:
        print("No ACCEPTED orders found to test.")
        return

    with open("test_output.txt", "w") as f:
        f.write(f"Testing with Order ID: {order.id}, Status: {order.status}\n")

        # Set a dummy checkout request ID if missing so we can match it
        checkout_id = order.checkout_request_id or "TEST_CHECKOUT_ID_123"
        order.checkout_request_id = checkout_id
        order.save()
        
        f.write(f"Using CheckoutRequestID: {checkout_id}\n")

        # Construct Payload
        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29123-34620541-1",
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1.00},
                            {"Name": "MpesaReceiptNumber", "Value": "TEST_RECEIPT_001"},
                            {"Name": "TransactionDate", "Value": 20191219102115},
                            {"Name": "PhoneNumber", "Value": 254700000000}
                        ]
                    }
                }
            }
        }

        # Send Request
        url = "http://127.0.0.1:8000/mpesa/callback/"
        try:
            response = requests.post(url, json=payload)
            f.write(f"Callback Response: {response.status_code} - {response.text}\n")
        except Exception as e:
            f.write(f"Error sending callback: {e}\n")

        # Verify Logic
        order.refresh_from_db()
        f.write(f"Final Order Status: {order.status}\n")
        
        if order.status == 'ESCROW':
            f.write("SUCCESS: Order status updated to ESCROW\n")
        else:
            f.write("FAILURE: Order status did NOT update\n")

if __name__ == "__main__":
    run()
