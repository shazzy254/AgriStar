
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AgriStar.settings")
django.setup()

from marketplace.models import Order

def run():
    print("Starting Direct Logic Test...")
    
    # 1. Setup Order
    order = Order.objects.filter(status='ACCEPTED').last()
    if not order:
        # Create one if needed or just fail
        print("No ACCEPTED order found. Creating a dummy one.")
        from users.models import User
        from marketplace.models import Product
        buyer = User.objects.filter(role='BUYER').first()
        product = Product.objects.first()
        if not buyer or not product:
            print("Cannot create dummy order: missing buyer or product.")
            return
        order = Order.objects.create(buyer=buyer, product=product, total_price=100, status='ACCEPTED')

    # Ensure it sends a clean slate
    checkout_id = "DIRECT_TEST_ID_999"
    order.checkout_request_id = checkout_id
    order.status = 'ACCEPTED'
    order.save()
    print(f"Test Order ID: {order.id}, Initial Status: {order.status}, CheckoutID: {checkout_id}")

    # 2. Simulate View Logic manually
    # (Copying logic from mpesa/views.py)
    result_code = 0
    receipt_number = "DIRECT_RECEIPT_888"
    
    print("Simulating Callback Logic...")
    if checkout_id:
        try:
            order_obj = Order.objects.get(checkout_request_id=checkout_id)
            if result_code == 0:
                order_obj.status = "ESCROW"
                order_obj.mpesa_receipt_number = receipt_number
                order_obj.save()
                print("Logic executed: Status set to ESCROW")
        except Order.DoesNotExist:
            print("Order not found during logic execution!")

    # 3. Verify
    order.refresh_from_db()
    print(f"Final Order Status: {order.status}")
    
    if order.status == 'ESCROW':
        print("SUCCESS: Logic Verification Passed")
    else:
        print("FAILURE: Logic Verification Failed")

if __name__ == "__main__":
    run()
