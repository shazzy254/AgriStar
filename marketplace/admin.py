from django.contrib import admin
from .models import Product, Order, CartItem, Notification, Favorite

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'category', 'location', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'location')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'buyer', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'buyer__username', 'product__name')

admin.site.register(CartItem)
admin.site.register(Notification)
admin.site.register(Favorite)
