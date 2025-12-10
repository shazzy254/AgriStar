
import os
import sys
import django

# Setup path to project root (one level up from scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from users.models import User, Profile, RiderProfile
from marketplace.models import Product, Order, Notification

def run_test():
    print("Setting up test data...")
    try:
        # Cleanup prev run
        User.objects.filter(username__in=['test_farmer', 'test_rider', 'test_buyer']).delete()
        
        # Create Test Users
        farmer = User.objects.create_user(username='test_farmer', password='password')
        farmer.role = 'FARMER'
        farmer.save()
        
        rider = User.objects.create_user(username='test_rider', password='password')
        rider.role = 'RIDER'
        rider.save()
        
        buyer = User.objects.create_user(username='test_buyer', password='password')
        buyer.role = 'BUYER'
        buyer.save()
        
        # Create products
        product = Product.objects.create(seller=farmer, name='Kale', price=10, category='VEGETABLES', location='Nairobi')
        
        # Create Order
        order = Order.objects.create(buyer=buyer, product=product, quantity=5, total_price=50, assigned_rider=rider)
        
        # Create CartItem
        from marketplace.models import CartItem
        CartItem.objects.create(buyer=buyer, product=product, quantity=1)
        
        # Create Review
        from users.review_models import FarmerReview
        FarmerReview.objects.create(farmer=farmer, buyer=buyer, rating=5, review_text="Good")
        
        # Create FavoriteFarmer M2M
        # Note: FavoriteFarmer model exists but Profile also has m2m field?
        # users/models.py: Profile.favorite_farmers = ManyToManyField(User...)
        # And there is a model FavoriteFarmer in models.py line 158 which is a through model or separate?
        # It looks like a separate model 'FavoriteFarmer' defined but Profile uses 'favorite_farmers' field which creates an implicit table if through not specified.
        # Let's check users/models.py line 61. It does NOT specify through='FavoriteFarmer'.
        # So 'FavoriteFarmer' model at line 158 might be redundant or legacy?
        # Let's populate the Profile m2m.
        buyer.profile.favorite_farmers.add(farmer)
        
        # Create DeliveryAddress
        from users.models import DeliveryAddress
        DeliveryAddress.objects.create(user=buyer, county="Nairobi", constituency="Westlands", ward="Parklands")

        print("Complex Data Created.")
        
        print("Testing Rider Deletion...", end="")
        rider.delete()
        print("OK")
        
        print("Testing Farmer Deletion (Complex)...", end="")
        farmer.delete()
        # This deletes Product.
        # Deletes Order (Cascade from Product).
        # Deletes CartItem (Cascade from Product).
        # Deletes FarmerReview (Cascade from Farmer).
        # Deletes Profile m2m relation (Cascade from User).
        print("OK")
        
        print("Testing Buyer Deletion...", end="")
        buyer.delete()
        print("OK")
        
        print("ALL TESTS PASSED")
        
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
