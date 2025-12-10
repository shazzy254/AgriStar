import os
import django
import sys
import json
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from marketplace.models import Order
from django.test import RequestFactory
from mpesa.views import mpesa_callback

def force_update():
    print("=== Force Update Order Payment Status (Manual Callback) ===")
    
    # List recent orders
    print("\nRecent Orders:")
    orders = Order.objects.all().order_by('-created_at')[:10]
    for order in orders:
        print(f"ID: {order.id} | Buyer: {order.buyer.username} | Total: {order.total_price} | Status: {order.status} | CheckoutID: {order.checkout_request_id}")
        
    order_id = input("\nEnter Order ID to Simulate Payment for: ")
    
    try:
        order = Order.objects.get(id=order_id)
        
        if not order.checkout_request_id:
            print("WARNING: Order has no CheckoutRequestID (Payment likely not initiated). Generating dummy one...")
            order.checkout_request_id = f"ws_CO_FORCE_{datetime.now().strftime('%H%M%S')}"
            order.save()
            
        print(f"Simulating M-Pesa Callback for Order #{order.id}...")
        
        # Create fake request
        factory = RequestFactory()
        callback_data = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "FORCE_UPDATE_REQ",
                    "CheckoutRequestID": order.checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "Forced success via script.",
                    "CallbackMetadata": {
                        "Item": [{"Name": "MpesaReceiptNumber", "Value": "FORCED_RECEIPT_123"}]
                    }
                }
            }
        }
        
        request = factory.post(
            '/mpesa/callback/', 
            data=json.dumps(callback_data), 
            content_type='application/json'
        )
        
        # Call the view directly
        response = mpesa_callback(request)
        
        order.refresh_from_db()
        print(f"\nResult: Order Status is now: {order.status}")
        if order.status == 'ESCROW':
            print("SUCCESS! You can now check the dashboard.")
        else:
            print("FAILURE: Status did not update. Check logic.")
            
    except Order.DoesNotExist:
        print("Order not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    force_update()
