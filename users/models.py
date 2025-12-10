from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = 'FARMER', _('Farmer')
        BUYER = 'BUYER', _('Buyer')
        SUPPLIER = 'SUPPLIER', _('Supplier')
        RIDER = 'RIDER', _('Rider')
        ADMIN = 'ADMIN', _('Admin')

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.FARMER
    )
    
    # Multilingual support preference
    language_preference = models.CharField(
        max_length=10, 
        choices=[('en', 'English'), ('sw', 'Kiswahili')], 
        default='en'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True, help_text="Public name to show (e.g. Farm Name)")
    bio = models.TextField(blank=True, max_length=500)
    location = models.CharField(max_length=100, blank=True, help_text="City/Area")
    address = models.CharField(max_length=200, blank=True, help_text="Street address")
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    is_verified = models.BooleanField(default=False)
    
    # For Farmers
    farm_size = models.CharField(max_length=50, blank=True, help_text="e.g. 5 acres")
    main_crops = models.CharField(max_length=200, blank=True, help_text="Comma separated")
    
    # For Suppliers
    company_name = models.CharField(max_length=100, blank=True)
    
    # For Buyers
    buyer_type = models.CharField(
        max_length=50, 
        blank=True, 
        choices=[
            ('MARKETPLACE', 'Marketplace Seller'),
            ('INDIVIDUAL', 'Individual Consumer'),
            ('RESTAURANT', 'Restaurant/Hotel'),
            ('RETAILER', 'Retail Shop'),
        ],
        help_text="Type of buyer"
    )
    favorite_farmers = models.ManyToManyField(
        User, 
        related_name='favorited_by_buyers', 
        blank=True, 
        # limit_choices_to={'role': User.Role.FARMER} # Can't use User.Role here easily if circular, but let's try 'FARMER' string or leave it for logic validation
    )
    business_name = models.CharField(max_length=100, blank=True, help_text="For marketplace sellers/businesses")
    marketplace_location = models.CharField(max_length=200, blank=True, help_text="Where your marketplace/business is located")
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class RiderProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        VERIFIED = 'VERIFIED', _('Verified')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    class VehicleType(models.TextChoices):
        MOTORBIKE = 'MOTORBIKE', _('Motorbike')
        TUKTUK = 'TUKTUK', _('TukTuk')
        PICKUP = 'PICKUP', _('Pickup')
        LORRY = 'LORRY', _('Lorry')
        BICYCLE = 'BICYCLE', _('Bicycle')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')
    id_number = models.CharField(max_length=20, blank=True, null=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    is_available = models.BooleanField(default=False)
    active_hours_start = models.TimeField(null=True, blank=True)
    active_hours_end = models.TimeField(null=True, blank=True)
    
    # Stats
    total_deliveries = models.IntegerField(default=0)
    completed_deliveries = models.IntegerField(default=0)
    cancelled_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Vehicle Info
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.MOTORBIKE)
    vehicle_plate_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"Rider: {self.user.username}"
        
    @property
    def delivery_success_rate(self):
        if self.total_deliveries == 0:
            return 0
        return int((self.completed_deliveries / self.total_deliveries) * 100)
    
    def get_full_location(self):
        return self.user.profile.location or "Location not set"

class DeliveryAddress(models.Model):
    """Model for buyer delivery addresses with Kenyan location details"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_addresses')
    label = models.CharField(max_length=50, blank=True, help_text="e.g., Home, Office")
    county = models.CharField(max_length=100)
    constituency = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    gps_coordinates = models.CharField(max_length=100, blank=True, help_text="Latitude, Longitude")
    additional_details = models.TextField(blank=True, help_text="Building name, floor, landmarks")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = "Delivery Addresses"
    
    def __str__(self):
        return f"{self.label or 'Address'} - {self.county}, {self.constituency}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset all other default addresses for this user
        if self.is_default:
            DeliveryAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rating}★ for {self.reviewed_user.username} by {self.reviewer.username}"

class FavoriteFarmer(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_farmers')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('buyer', 'farmer')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        if instance.role == User.Role.RIDER:
            RiderProfile.objects.create(user=instance)
        # Create FarmerBadge for farmers
        if instance.role == User.Role.FARMER:
            from users.review_models import FarmerBadge
            FarmerBadge.objects.create(farmer=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    if instance.role == User.Role.RIDER and hasattr(instance, 'rider_profile'):
        instance.rider_profile.save()
