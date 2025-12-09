from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

User = get_user_model()

class FarmerReview(models.Model):
    """Reviews for farmers by buyers"""
    farmer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='farmer_reviews',
        limit_choices_to={'role': 'FARMER'}
    )
    buyer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='buyer_reviews',
        limit_choices_to={'role': 'BUYER'}
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    review_text = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['farmer', 'buyer']  # One review per buyer per farmer
        verbose_name = 'Farmer Review'
        verbose_name_plural = 'Farmer Reviews'
    
    def __str__(self):
        return f"{self.buyer.username} → {self.farmer.username} ({self.rating}★)"


class FarmerBadge(models.Model):
    """Verification badges for farmers based on their activity level"""
    
    BADGE_LEVELS = [
        ('BEGINNER', 'Beginner Farmer'),
        ('BRONZE', 'Bronze Farmer'),
        ('SILVER', 'Silver Farmer'),
        ('GOLD', 'Gold Farmer'),
        ('PLATINUM', 'Platinum Farmer'),
        ('DIAMOND', 'Diamond Farmer'),
    ]
    
    farmer = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='farmer_badge',
        limit_choices_to={'role': 'FARMER'}
    )
    badge_level = models.CharField(
        max_length=20,
        choices=BADGE_LEVELS,
        default='BEGINNER'
    )
    total_sales = models.IntegerField(default=0)
    total_products = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    earned_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Farmer Badge'
        verbose_name_plural = 'Farmer Badges'
    
    def __str__(self):
        return f"{self.farmer.username} - {self.get_badge_level_display()}"
    
    def update_badge_level(self):
        """Update badge level based on criteria"""
        # Calculate average rating
        avg_rating = self.farmer.farmer_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        self.average_rating = round(avg_rating, 2)
        self.total_reviews = self.farmer.farmer_reviews.count()
        
        # Badge level criteria
        if self.total_sales >= 1000 and self.average_rating >= 4.8 and self.total_products >= 50:
            self.badge_level = 'DIAMOND'
        elif self.total_sales >= 500 and self.average_rating >= 4.5 and self.total_products >= 30:
            self.badge_level = 'PLATINUM'
        elif self.total_sales >= 250 and self.average_rating >= 4.0 and self.total_products >= 20:
            self.badge_level = 'GOLD'
        elif self.total_sales >= 100 and self.average_rating >= 3.5 and self.total_products >= 10:
            self.badge_level = 'SILVER'
        elif self.total_sales >= 25 and self.average_rating >= 3.0 and self.total_products >= 5:
            self.badge_level = 'BRONZE'
        else:
            self.badge_level = 'BEGINNER'
        
        self.save()
    
    def get_badge_color(self):
        """Return badge color for display"""
        colors = {
            'BEGINNER': '#9CA3AF',  # Gray
            'BRONZE': '#CD7F32',    # Bronze
            'SILVER': '#C0C0C0',    # Silver
            'GOLD': '#FFD700',      # Gold
            'PLATINUM': '#E5E4E2',  # Platinum
            'DIAMOND': '#B9F2FF',   # Diamond Blue
        }
        return colors.get(self.badge_level, '#9CA3AF')
    
    def get_badge_icon(self):
        """Return badge icon"""
        icons = {
            'BEGINNER': '🌱',
            'BRONZE': '🥉',
            'SILVER': '🥈',
            'GOLD': '🥇',
            'PLATINUM': '💎',
            'DIAMOND': '💠',
        }
        return icons.get(self.badge_level, '🌱')
