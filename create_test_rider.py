import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from users.models import User, RiderProfile
from marketplace.models import Order, Product
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_data():
    print("Creating test rider...")
    # Create Rider
    rider, created = User.objects.get_or_create(username='rider1', email='rider1@example.com')
    if created:
        rider.set_password('password123')
        rider.role = User.Role.RIDER
        rider.save()
        print(f"Rider {rider.username} created.")
    else:
        print(f"Rider {rider.username} already exists.")

    # Ensure Rider Profile exists and is set
    if not hasattr(rider, 'rider_profile'):
        RiderProfile.objects.create(user=rider)
    
    rider.rider_profile.is_available = True
    rider.rider_profile.vehicle_type = 'MOTORBIKE'
    rider.rider_profile.current_latitude = -1.2921 # Nairobi
    rider.rider_profile.current_longitude = 36.8219
    rider.rider_profile.save()
    print("Rider profile updated (Available, Nairobi).")

    # Ensure Farmer exists (shazzy)
    try:
        farmer = User.objects.get(username='shazzy')
        print(f"Farmer {farmer.username} found.")
    except User.DoesNotExist:
        print("Farmer 'shazzy' not found. Creating...")
        farmer = User.objects.create_user('shazzy', 'shazzy@example.com', 'password123')
        farmer.role = User.Role.FARMER
        farmer.save()

    # Create a product for farmer if none
    product, created = Product.objects.get_or_create(
        seller=farmer,
        name='Test Tomatoes',
        defaults={
            'price': 100,
            'category': 'VEGETABLES',
            'description': 'Fresh tomatoes',
            'location': 'Nairobi',
            'unit': 'kg'
        }
    )

    # Create a buyer
    buyer, created = User.objects.get_or_create(username='buyer1', email='buyer1@example.com')
    if created:
        buyer.set_password('password123')
        buyer.role = User.Role.BUYER
        buyer.save()

    # Create an ACCEPTED order for this product
    order = Order.objects.create(
        buyer=buyer,
        product=product,
        quantity=5,
        status='ACCEPTED',
        total_price=500
    )
    print(f"Created test order #{order.id} (ACCEPTED) for {farmer.username}.")

if __name__ == '__main__':
    create_test_data()
