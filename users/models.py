from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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
    
    # Location Coordinates & Hierarchy
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    county = models.ForeignKey('County', on_delete=models.SET_NULL, null=True, blank=True)
    sub_county = models.ForeignKey('SubCounty', on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey('Ward', on_delete=models.SET_NULL, null=True, blank=True)
    
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
        REJECTED = 'REJECTED', _('Rejected')

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
    
    # Personal Info
    id_number = models.CharField(max_length=20, blank=True, null=True)
    license_number = models.CharField(max_length=20, blank=True, null=True)
    passport_photo = models.ImageField(upload_to='rider_passports/', blank=True, null=True)
    
    # Verification Documents
    verification_id_front = models.ImageField(upload_to='rider_verification/', blank=True, null=True)
    verification_id_back = models.ImageField(upload_to='rider_verification/', blank=True, null=True)
    verification_selfie = models.ImageField(upload_to='rider_verification/', blank=True, null=True)
    verification_license = models.ImageField(upload_to='rider_verification/', blank=True, null=True)
    verification_good_conduct = models.ImageField(upload_to='rider_verification/', blank=True, null=True)
    
    def __str__(self):
        return f"Rider: {self.user.username}"
        
    @property
    def delivery_success_rate(self):
        if self.total_deliveries == 0:
            return 0
        return int((self.completed_deliveries / self.total_deliveries) * 100)
    
    def get_full_location(self):
        return self.user.profile.location or "Location not set"


class RiderReview(models.Model):
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rider_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_rider_reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.rider.username} by {self.reviewer.username}"

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

# Location Hierarchy Models (Kenya)
class County(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.IntegerField(unique=True, help_text="County Code (e.g., 047 for Nairobi)")
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Counties"
        
    def __str__(self):
        return f"{self.code} - {self.name}"

class SubCounty(models.Model):
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='sub_counties')
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Sub Counties"
        unique_together = ('county', 'name')
        
    def __str__(self):
        return f"{self.name}, {self.county.name}"

class Ward(models.Model):
    sub_county = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='wards')
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['name']
        unique_together = ('sub_county', 'name')
        
    def __str__(self):
        return f"{self.name} (Ward)"

class VehicleChangeRequest(models.Model):
    """Model for tracking rider vehicle information change requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_change_requests')
    
    # Old values
    old_vehicle_type = models.CharField(max_length=20, blank=True)
    old_vehicle_plate = models.CharField(max_length=20, blank=True)
    old_license_number = models.CharField(max_length=50, blank=True)
    
    # Requested new values
    new_vehicle_type = models.CharField(max_length=20)
    new_vehicle_plate = models.CharField(max_length=20)
    new_license_number = models.CharField(max_length=50, blank=True)
    
    # Request details
    reason = models.TextField(help_text="Reason for change request")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True, help_text="Admin's notes on approval/rejection")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vehicle_changes')
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Vehicle Change Request"
        verbose_name_plural = "Vehicle Change Requests"
    
    def __str__(self):
        return f"Vehicle change request by {self.rider.username} - {self.status}"
    
    def approve(self, admin_user, notes=""):
        """Approve the change request and update rider profile"""
        self.status = 'APPROVED'
        self.admin_notes = notes
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update rider profile
        rider_profile = self.rider.rider_profile
        rider_profile.vehicle_type = self.new_vehicle_type
        rider_profile.vehicle_plate_number = self.new_vehicle_plate
        rider_profile.license_number = self.new_license_number
        rider_profile.save()
    
    def reject(self, admin_user, notes=""):
        """Reject the change request"""
        self.status = 'REJECTED'
        self.admin_notes = notes
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

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
