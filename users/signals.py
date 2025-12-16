from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from marketplace.models import Product, Order
from users.review_models import FarmerReview, FarmerBadge

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def update_badge_on_product_change(sender, instance, **kwargs):
    """Update farmer badge when products are added/removed"""
    if instance.seller and instance.seller.role == 'FARMER':
        # Get or create badge to be safe
        badge, _ = FarmerBadge.objects.get_or_create(farmer=instance.seller)
        badge.update_badge_level()

@receiver(post_save, sender=Order)
def update_badge_on_order_change(sender, instance, **kwargs):
    """Update farmer badge when order status changes (sales count)"""
    if instance.product.seller and instance.product.seller.role == 'FARMER':
        # Only certain statuses affect the count, but calling update is cheap enough
        # and safer than duplicating logic here.
        badge, _ = FarmerBadge.objects.get_or_create(farmer=instance.product.seller)
        badge.update_badge_level()

@receiver(post_save, sender=FarmerReview)
def update_badge_on_review(sender, instance, **kwargs):
    """Update farmer badge when a review is added"""
    # instance.farmer is the User (farmer)
    badge, _ = FarmerBadge.objects.get_or_create(farmer=instance.farmer)
    badge.update_badge_level()
