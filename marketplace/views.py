from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from rest_framework import viewsets, filters, permissions
from .models import Product, Order, CartItem, Favorite, Notification
from .serializers import ProductSerializer, OrderSerializer
from .forms import ProductForm # We need to create this
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
    
    # For this flow, we'll redirect to the payment page for the first order created
    # In a real multi-order scenario, we might want a 'My Orders' page to pay for them individually or a batch payment.
    # For simplicity, let's assume we redirect to the dashboard where they can see orders and pay, 
    # OR if we want to force payment immediately, we pick the last created order.
    
    # Let's redirect to dashboard with a success message, and they can click 'Pay' on the order.
    # OR, to follow the user's flow "Shows a Proceed to Payment page", we can redirect to a payment page for the batch?
    # The user said "Buyer clicks Order Now -> Creates Order Object -> Shows Proceed to Payment page".
    # Since we might have multiple orders from a cart, let's redirect to the dashboard for now, 
    # but maybe we should grab the last order and redirect to its payment page if it was a single item checkout.
    
    if orders_created == 1:
        # If single order, go straight to payment
        # order = Order.objects.filter(buyer=request.user).order_by('-created_at').first()
        # return redirect('payment_page', order_id=order.id)
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
    # If user doesn't have phone number in profile, we might need to ask for it.
    # For now, let's assume we get it from POST or user profile.
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
    
    if order.status != 'ESCROW':
        return JsonResponse({'success': False, 'message': 'Order is not in Escrow state.'}, status=400)

    # Update status to Delivered (or directly to PAID_OUT as per user flow step 6)
    # User said: Buyer clicks "Confirm Delivery" -> System Calls B2C -> Updates order.status = "PAID_OUT"
    
    try:
        # Release funds to farmer
        # We need farmer's phone number. Assuming it's in the profile.
        farmer_phone = order.product.seller.profile.phone_number if hasattr(order.product.seller, 'profile') else ''
        if not farmer_phone:
             return JsonResponse({'success': False, 'message': 'Farmer phone number not found.'}, status=400)
             
        # Format farmer phone
        if farmer_phone.startswith('0'):
            farmer_phone = '254' + farmer_phone[1:]

        # Call B2C
        # In a real app, you might want to do this asynchronously (Celery) or verify the B2C response carefully.
        # For this demo, we call it directly.
        response = release_escrow_to_farmer(farmer_phone, int(order.total_price))
        
        # Check if B2C request was accepted (ConversationID/OriginatorConversationID present)
        if response.get('ConversationID'):
            order.status = 'PAID_OUT'
            order.save()
            
            # Notify Farmer
            Notification.objects.create(
                user=order.product.seller,
                notification_type='ORDER_COMPLETED', # Add this type to choices if needed
                order=order,
                message=f'Order #{order.id} delivered and funds released to your M-Pesa.'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Delivery confirmed and funds released to farmer.'
            })
        else:
             return JsonResponse({'success': False, 'message': 'Failed to release funds. Please contact support.'}, status=500)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

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
