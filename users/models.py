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
    bio = models.TextField(blank=True, max_length=500)
    location = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    is_verified = models.BooleanField(default=False)
    
    # For Farmers
    farm_size = models.CharField(max_length=50, blank=True, help_text="e.g. 5 acres")
    main_crops = models.CharField(max_length=200, blank=True, help_text="Comma separated")
    
    # For Suppliers
    company_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
