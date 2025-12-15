from django.db import models
from django.conf import settings

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('VEGETABLES', 'Vegetables'),
        ('FRUITS', 'Fruits'),
        ('GRAINS', 'Grains'),
        ('LIVESTOCK', 'Livestock'),
        ('EQUIPMENT', 'Equipment'),
        ('SEEDS', 'Seeds'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    location = models.CharField(max_length=100)
    unit = models.CharField(
        max_length=50, 
        help_text="e.g. kg, litre, crate, tray, piece",
        default='kg'
    )
    available = models.BooleanField(default=True)
    approval_status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    quantity = models.PositiveIntegerField(default=1)
    freshness_notes = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    old_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} stock update ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


from users.models import DeliveryAddress

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('ESCROW', 'Escrow (Paid)'),
        ('IN_DELIVERY', 'In Delivery'),
        ('DELIVERED', 'Delivered'),
        ('PAID_OUT', 'Paid Out to Farmer'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('DISPUTED', 'Disputed'),
        ('REFUNDED', 'Refunded'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('PICKUP', 'Pickup (Buyer collects)'),
        ('DELIVERY', 'Delivery (Rider needed)'),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, default='PICKUP')
    delivery_address = models.ForeignKey(DeliveryAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', help_text="Buyer's delivery address for this order")
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    assigned_rider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_delivery_time = models.CharField(max_length=50, blank=True, null=True, help_text="E.g. 30 mins")
    delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_ready_for_pickup = models.BooleanField(default=False, help_text="Marked by farmer when ready for rider")
    pickup_verification_code = models.CharField(max_length=6, blank=True, null=True, help_text="Code rider scans/enters to confirm pickup")
    delivery_verification_code = models.CharField(max_length=6, blank=True, null=True, help_text="Code buyer scans/enters to confirm delivery")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.product.name}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class CartItem(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='in_carts')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'product')
        ordering = ['-added_at']

    @property
    def total_price(self):
        return self.product.price * self.quantity

    @property
    def farmer(self):
        return self.product.seller

    def __str__(self):
        return f"{self.buyer.username}'s cart - {self.product.name} (x{self.quantity})"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ORDER_PLACED', 'Order Placed'),
        ('ORDER_ACCEPTED', 'Order Accepted'),
        ('ORDER_REJECTED', 'Order Rejected'),
        ('ORDER_ASSIGNED', 'Order Assigned'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {'Read' if self.is_read else 'Unread'}"
