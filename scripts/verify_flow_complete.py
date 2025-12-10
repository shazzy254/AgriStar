import os
import django
import sys
from unittest.mock import patch, MagicMock

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from users.models import User, Profile
from marketplace.models import Order, Product
from mpesa.views import mpesa_callback
from marketplace.views import update_order_status
from django.test import RequestFactory
import json

def run_test():
    print("=== Starting End-to-End Flow Verification ===")
    
    # 1. Setup Users
    buyer, _ = User.objects.get_or_create(username='test_buyer_flow', email='buyer@flow.com', role=User.Role.BUYER)
    farmer, _ = User.objects.get_or_create(username='test_farmer_flow', email='farmer@flow.com', role=User.Role.FARMER)
    rider, _ = User.objects.get_or_create(username='test_rider_flow', email='rider@flow.com', role=User.Role.RIDER)
    
    # Ensure profiles exist
    if not hasattr(farmer, 'profile'): Profile.objects.create(user=farmer, phone_number='0712345678')
    if not hasattr(buyer, 'profile'): Profile.objects.create(user=buyer)
    
    # 2. Setup Product and Order
    product, _ = Product.objects.get_or_create(
        seller=farmer, name='Flow Test Product', price=1000, category='VEGETABLES'
    )
    
    import time
    unique_checkout_id = f"ws_CO_TEST_{int(time.time()*1000)}"
    order = Order.objects.create(
        buyer=buyer,
        product=product,
        quantity=1,
        total_price=1000,
        status='ACCEPTED',
        checkout_request_id=unique_checkout_id,
        assigned_rider=rider
    )
    # Force save to be super sure
    order.save()
    
    print(f"1. Order Created: ID #{order.id}, Status: {order.status}")
    
    # 3. Simulate Payment Callback (ACCEPTED -> ESCROW)
    print("\n2. Simulating M-Pesa Callback...")
    factory = RequestFactory()
    callback_data = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": unique_checkout_id,
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [{"Name": "MpesaReceiptNumber", "Value": "TEST_RECEIPT"}]
                }
            }
        }
    }
    
    request = factory.post(
        '/mpesa/callback/', 
        data=json.dumps(callback_data), 
        content_type='application/json'
    )
    
    from mpesa.views import mpesa_callback
    response = mpesa_callback(request)
    
    order.refresh_from_db()
    if order.status == 'ESCROW' and order.mpesa_receipt_number == 'TEST_RECEIPT':
        print("   SUCCESS: Order updated to ESCROW via callback")
    else:
        print(f"   FAILURE: Order status is {order.status}")
        return

    # 4. Simulate Rider 'Start Delivery' (ESCROW -> IN_DELIVERY)
    print("\n3. Simulating Rider Start Delivery...")
    request = factory.post('/marketplace/order/update-status/', {'status': 'IN_DELIVERY'})
    request.user = rider # Authenticate as rider
    
    from marketplace.views import update_order_status
    # We need to add messsages middleware mock or similar, but RequestFactory doesn't have it by default
    # So we'll patch messages
    
    with patch('marketplace.views.messages') as mock_messages:
         update_order_status(request, order.id)
         
    order.refresh_from_db()
    if order.status == 'IN_DELIVERY':
        print("   SUCCESS: Order updated to IN_DELIVERY")
    else:
        print(f"   FAILURE: Order status is {order.status}")
        return

    # 5. Simulate Rider 'Mark Delivered' (IN_DELIVERY -> DELIVERED)
    print("\n4. Simulating Rider Mark Delivered...")
    request = factory.post('/marketplace/order/update-status/', {'status': 'DELIVERED'})
    request.user = rider
    
    with patch('marketplace.views.messages') as mock_messages:
         update_order_status(request, order.id)
         
    order.refresh_from_db()
    if order.status == 'DELIVERED':
        print("   SUCCESS: Order updated to DELIVERED")
    else:
        print(f"   FAILURE: Order status is {order.status}")
        return

    # 6. Simulate Buyer 'Confirm Delivery' (DELIVERED -> PAID_OUT)
    print("\n5. Simulating Buyer Confirm Delivery (Releasing Funds)...")
    request = factory.get(f'/marketplace/confirm-delivery/{order.id}/') # It's a GET or POST? views.py uses GET usually for links, checking...
    # views.confirm_delivery checks order but doesn't specify method, so GET is fine.
    request.user = buyer
    
    # Mock release_escrow_to_farmer to return success
    with patch('marketplace.views.release_escrow_to_farmer') as mock_release:
        mock_release.return_value = {
            'ConversationID': 'AG_2023_TEST',
            'OriginatorConversationID': '1234-5678',
            'ResponseCode': '0'
        }
        with patch('marketplace.views.messages') as mock_messages:
            from marketplace.views import confirm_delivery
            confirm_delivery(request, order.id)
            
    order.refresh_from_db()
    
    if order.status == 'PAID_OUT':
        print("   SUCCESS: Order updated to PAID_OUT")
    else:
        print(f"   FAILURE: Order status is {order.status}")
        return

    print("\n=== All Verification Steps Passed Successfully ===")

if __name__ == '__main__':
    run_test()
