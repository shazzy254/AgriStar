from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from rest_framework import viewsets, filters, permissions
from users.models import User
from .models import Product, Order, CartItem, Favorite, Notification
from .serializers import ProductSerializer, OrderSerializer
from .forms import ProductForm
from itertools import groupby
from operator import attrgetter
from mpesa.utils import release_escrow_to_farmer, stk_push

# API ViewSets
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category', 'location']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'FARMER': # Seller sees orders for their products
            return Order.objects.filter(product__seller=user)
        return Order.objects.filter(buyer=user) # Buyer sees their orders

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

# Template Views
def product_list(request):
    products = Product.objects.filter(available=True)
    # Simple search
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)
    return render(request, 'marketplace/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'marketplace/product_detail.html', {'product': product})

@login_required
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'marketplace/product_form.html', {'form': form})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Ensure only the owner can edit
    if request.user != product.seller:
        messages.error(request, "You do not have permission to edit this product.")
        return redirect('product_detail', pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('product_detail', pk=pk)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'marketplace/product_form.html', {'form': form, 'title': 'Edit Product'})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Ensure only the owner can delete
    if request.user != product.seller:
        messages.error(request, "You do not have permission to delete this product.")
        return redirect('product_detail', pk=pk)

    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('profile')
    
    return render(request, 'marketplace/product_confirm_delete.html', {'product': product})

# ==================== CART VIEWS ====================

@login_required
def add_to_cart(request, product_id):
    """Add product to cart or update quantity if already exists"""
    product = get_object_or_404(Product, id=product_id, available=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    cart_item, created = CartItem.objects.get_or_create(
        buyer=request.user,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    cart_count = request.user.cart_items.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_count': cart_count
        })
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_list')

@login_required
def view_cart(request):
    """Display cart items grouped by farmer"""
    cart_items = request.user.cart_items.select_related('product', 'product__seller').all()
    
    # Group cart items by farmer
    cart_items_sorted = sorted(cart_items, key=lambda x: x.farmer.id)
    grouped_items_list = []
    
    for farmer_id, items in groupby(cart_items_sorted, key=lambda x: x.farmer):
        items_list = list(items)
        farmer = items_list[0].farmer
        subtotal = sum(item.total_price for item in items_list)
        
        grouped_items_list.append({
            'farmer': farmer,
            'items': items_list,
            'subtotal': subtotal
        })
    
    # Calculate totals
    cart_total = sum(item.total_price for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)
    
    context = {
        'grouped_items': grouped_items_list,
        'cart_total': cart_total,
        'total_items': total_items,
    }
    return render(request, 'marketplace/cart.html', context)

@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, buyer=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
    
    cart_item.quantity = quantity
    cart_item.save()
    
    cart_total = sum(item.total_price for item in request.user.cart_items.all())
    
    return JsonResponse({
        'success': True,
        'item_total': float(cart_item.total_price),
        'cart_total': float(cart_total)
    })

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, buyer=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    cart_count = request.user.cart_items.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_count': cart_count
        })
    
    messages.success(request, f'{product_name} removed from cart')
    return redirect('view_cart')

@login_required
def checkout_cart(request):
    """Convert cart items to orders and clear cart"""
    if request.method != 'POST':
        return redirect('view_cart')
    
    cart_items = request.user.cart_items.select_related('product').all()
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('view_cart')
    
    # Create orders (one per cart item)
    orders_created = 0
    for item in cart_items:
        if item.product.available:
            order = Order.objects.create(
                buyer=request.user,
                product=item.product,
                quantity=item.quantity,
                status='PENDING'
            )
            
            # Create notification for buyer
            Notification.objects.create(
                user=request.user,
                notification_type='ORDER_PLACED',
                order=order,
                message=f'Your order for {item.product.name} (x{item.quantity}) has been placed successfully!'
            )

            # Create notification for farmer (seller)
            Notification.objects.create(
                user=item.product.seller,
                notification_type='ORDER_PLACED',
                order=order,
                message=f'New order received: {item.product.name} (x{item.quantity}) from {request.user.username}'
            )
            
            orders_created += 1
    
    # Clear cart
    cart_items.delete()
    
    if orders_created == 1:
        # If single order, check logic here if needed
        pass

    messages.success(request, f'{orders_created} order(s) placed successfully! Waiting for farmer approval.')
    return redirect('dashboard')

@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    return render(request, 'marketplace/payment.html', {'order': order})

@login_required
def initiate_payment(request, order_id):
    if request.method != "POST":
        return redirect('dashboard')
        
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    # Phone number is in Profile model
    phone_number = request.user.profile.phone_number if hasattr(request.user, 'profile') else ''
    
    phone = request.POST.get('phone', phone_number)
    
    if not phone:
        messages.error(request, "Phone number is required for M-Pesa payment.")
        return redirect('payment_page', order_id=order.id)
        
    # Format phone number to 254...
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # Call STK Push
    try:
        response = stk_push(phone, int(order.total_price), account_reference=f"Order-{order.id}")
        
        # Save CheckoutRequestID to order for tracking callback
        checkout_request_id = response.get('CheckoutRequestID')
        if checkout_request_id:
            order.checkout_request_id = checkout_request_id
            order.save()
            messages.success(request, "M-Pesa STK Push sent! Please check your phone to complete payment.")
        else:
            messages.error(request, "Failed to initiate M-Pesa payment. Please try again.")
            
    except Exception as e:
        messages.error(request, f"Error initiating payment: {str(e)}")
        
    return redirect('payment_page', order_id=order.id)

@login_required
def confirm_delivery(request, order_id):
    """Confirm delivery of an order"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    allowed_statuses = ['ESCROW', 'IN_DELIVERY', 'DELIVERED']
    if order.status not in allowed_statuses:
        messages.error(request, 'Order is not in a valid state for delivery confirmation (Escrow/Delivery).')
        return redirect('dashboard')

    try:
        # Release funds to farmer
        farmer_phone = order.product.seller.profile.phone_number if hasattr(order.product.seller, 'profile') else ''
        if not farmer_phone:
             return JsonResponse({'success': False, 'message': 'Farmer phone number not found.'}, status=400)
             
        # Format farmer phone
        if farmer_phone.startswith('0'):
            farmer_phone = '254' + farmer_phone[1:]

        # Call B2C
        response = release_escrow_to_farmer(farmer_phone, int(order.total_price))
        
        # Check if B2C request was accepted (ConversationID/OriginatorConversationID present)
        if response.get('ConversationID'):
            order.status = 'PAID_OUT'
            order.save()
            
            # Notify Farmer
            Notification.objects.create(
                user=order.product.seller,
                notification_type='ORDER_COMPLETED', 
                order=order,
                message=f'Order #{order.id} delivered and funds released to your M-Pesa.'
            )
            
            messages.success(request, 'Delivery confirmed! Funds successfully released to farmer.')
            return redirect('dashboard')
        else:
             messages.error(request, 'Failed to release funds. Please contact support.')
             return redirect('dashboard')

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

@login_required
def view_saved_products(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    products = [fav.product for fav in favorites]
    return render(request, 'marketplace/saved_products.html', {'products': products})

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        message = 'Removed from favorites'
        is_favorite = False
    else:
        message = 'Added to favorites'
        is_favorite = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': message, 'is_favorite': is_favorite})
        
    messages.success(request, message)
    return redirect('product_detail', pk=product_id)

@login_required
def view_notifications(request):
    notifications = request.user.notifications.all()
    return render(request, 'marketplace/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    return redirect('view_notifications')

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    messages.success(request, 'All notifications marked as read')
    return redirect('view_notifications')


@login_required
def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    if order.status == 'PENDING':
        order.status = 'ACCEPTED'
        order.save()
        
        # Notify buyer
        Notification.objects.create(
            user=order.buyer,
            notification_type='ORDER_ACCEPTED',
            order=order,
            message=f"Your order for {order.product.name} has been accepted! You can now proceed to payment."
        )
        messages.success(request, f"Order #{order.id} accepted.")
    return redirect('dashboard')

@login_required
def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    if order.status == 'PENDING':
        order.status = 'REJECTED'
        order.save()
        
        # Notify buyer
        Notification.objects.create(
            user=order.buyer,
            notification_type='ORDER_REJECTED',
            order=order,
            message=f"Your order for {order.product.name} has been rejected."
        )
        messages.warning(request, f"Order #{order.id} rejected.")
    return redirect('dashboard')

@login_required
def find_rider(request, order_id):
    """View to search for available riders for a specific order"""
    order = get_object_or_404(Order, id=order_id)
    # Ensure current user is the seller
    if order.product.seller != request.user:
        messages.error(request, "Permission denied")
        return redirect('dashboard')
        
    riders = User.objects.filter(role=User.Role.RIDER, rider_profile__is_available=True)
    
    location_query = request.GET.get('location')
    if location_query:
        # Search by profile location (simple text match)
        riders = riders.filter(profile__location__icontains=location_query)
        
    context = {
        'order': order,
        'riders': riders,
        'search_query': location_query
    }
    return render(request, 'marketplace/find_rider.html', context)

@login_required
def assign_rider(request, order_id, rider_id):
    """Assign a rider to an order"""
    order = get_object_or_404(Order, id=order_id)
    if order.product.seller != request.user:
        messages.error(request, "Permission denied")
        return redirect('dashboard')
        
    rider = get_object_or_404(User, id=rider_id, role=User.Role.RIDER)
    
    order.assigned_rider = rider
    # Update status to ACCEPTED if it was PENDING -> This signifies the farmer has 'processed' it
    if order.status == 'PENDING':
        order.status = 'ACCEPTED'
        
    order.save()
    
    # Notify Rider
    Notification.objects.create(
        user=rider,
        notification_type='ORDER_ASSIGNED',
        order=order,
        message=f"New delivery assigned! Order #{order.id} - {order.product.name} from {order.product.seller.username}"
    )
    
    messages.success(request, f"Rider {rider.username} assigned to Order #{order.id}")
    return redirect('dashboard')
@login_required
def update_order_status(request, order_id):
    """Rider updates order status (e.g. In Delivery, Delivered)"""
    if request.method != 'POST':
        return redirect('dashboard')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Ensure current user is the assigned rider
    if order.assigned_rider != request.user:
        messages.error(request, "Permission denied. You are not the assigned rider.")
        return redirect('dashboard')
        
    new_status = request.POST.get('status')
    
    if new_status == 'IN_DELIVERY':
        if order.status in ['ACCEPTED', 'ESCROW']:
            # Prioritize ESCROW if it was already paid, but IN_DELIVERY is a tracking state
            # If we overwrite ESCROW, we might lose the 'paid' state visibility in some logic if not careful.
            # However, our models allow IN_DELIVERY. 
            # Ideally, IN_DELIVERY implies it's moving.
            order.status = 'IN_DELIVERY'
            order.save()
            
            # Notify Buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='ORDER_UPDATE',
                order=order,
                message=f"Rider is on the way! Your order #{order.id} is now in delivery."
            )
            messages.success(request, "Order marked as In Delivery.")
            
    elif new_status == 'DELIVERED':
        if order.status == 'IN_DELIVERY' or order.status == 'ESCROW':
            order.status = 'DELIVERED'
            order.save()
            
            # Notify Buyer to confirm
            Notification.objects.create(
                user=order.buyer,
                notification_type='ORDER_DELIVERED',
                order=order,
                message=f"Rider arriving! Please confirm delivery on your dashboard to release funds."
            )
            messages.success(request, "Order marked as Delivered.")
            
    return redirect('dashboard')
