import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from marketplace.models import Order, Notification

try:
    order = Order.objects.get(id=24)
    print(f"Order #{order.id} Status: {order.status}")
    
    seller = order.product.seller
    print(f"Seller: {seller.username}")
    
    print("\n--- Latest 3 Notifications for Seller ---")
    notifications = Notification.objects.filter(user=seller).order_by('-created_at')[:3]
    for n in notifications:
        print(f"[{n.created_at.strftime('%Y-%m-%d %H:%M:%S')}] Type: {n.notification_type}")
        print(f"Message: {n.message}")
        print("-" * 20)

except Exception as e:
    print(f"Error: {e}")
