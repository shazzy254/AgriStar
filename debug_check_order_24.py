import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from marketplace.models import Order, Notification

try:
    order = Order.objects.get(id=24)
    print(f"Order #{order.id}")
    print(f"Status: {order.status}")
    print(f"Buyer: {order.buyer.username}")
    print(f"Seller: {order.product.seller.username}")
    
    print("\n--- Seller Notifications ---")
    notifications = Notification.objects.filter(user=order.product.seller).order_by('-created_at')[:5]
    for n in notifications:
        print(f"[{n.created_at}] {n.notification_type}: {n.message}")

except Order.DoesNotExist:
    print("Order #24 not found.")
