import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from marketplace.models import Order

try:
    order = Order.objects.get(id=12)
    print(f"Order ID: {order.id}")
    print(f"Status: {order.status}")
    print(f"Product: {order.product.name}")
    print(f"Seller (Farmer): {order.product.seller.username}")
    
    if hasattr(order.product.seller, 'profile'):
        print(f"Farmer Phone: {order.product.seller.profile.phone_number}")
    else:
        print("Farmer has no profile.")
        
except Order.DoesNotExist:
    print("Order #12 not found.")
