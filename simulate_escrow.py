import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from marketplace.models import Order

# Get the latest order
try:
    latest_order = Order.objects.latest('created_at')
    print(f"Found Order #{latest_order.id}")
    print(f"Current Status: {latest_order.status}")
    print(f"Product: {latest_order.product.name}")
    print(f"Buyer: {latest_order.buyer.username}")
    
    # Update to ESCROW
    latest_order.status = 'ESCROW'
    latest_order.save()
    
    print(f"\nSUCCESS: Order #{latest_order.id} updated to ESCROW status.")
    print("You should now see the 'Confirm Delivery' button on the dashboard.")
    
except Order.DoesNotExist:
    print("No orders found in the database.")
except Exception as e:
    print(f"Error: {e}")
