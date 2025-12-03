from rest_framework import serializers
from .models import Product, Order

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')

    class Meta:
        model = Product
        fields = ['id', 'seller', 'seller_name', 'name', 'description', 'price', 'category', 'image', 'location', 'available', 'created_at']
        read_only_fields = ['seller']

class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    buyer_name = serializers.ReadOnlyField(source='buyer.username')

    class Meta:
        model = Order
        fields = ['id', 'buyer', 'buyer_name', 'product', 'product_name', 'quantity', 'total_price', 'status', 'created_at']
        read_only_fields = ['buyer', 'total_price']
