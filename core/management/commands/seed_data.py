from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import Product

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        # Create Users
        farmer, _ = User.objects.get_or_create(username='farmer_joe', role='FARMER', email='joe@farm.com')
        farmer.set_password('password123')
        farmer.save()
        
        buyer, _ = User.objects.get_or_create(username='buyer_ann', role='BUYER', email='ann@market.com')
        buyer.set_password('password123')
        buyer.save()
        
        # Create Product (without image for seed data)
        product, created = Product.objects.get_or_create(
            seller=farmer,
            defaults={
                'name': 'Fresh Tomatoes',
                'description': 'Organic red tomatoes from local farm',
                'price': 50.00,
                'category': 'VEGETABLES',
                'location': 'Nairobi',
                'available': True
            }
        )
        
        # Create another product
        Product.objects.get_or_create(
            seller=farmer,
            defaults={
                'name': 'Maize Seeds',
                'description': 'High-yield hybrid maize seeds',
                'price': 120.00,
                'category': 'SEEDS',
                'location': 'Nakuru',
                'available': True
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
