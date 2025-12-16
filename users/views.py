from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum
from decimal import Decimal
from .forms import (
    RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm,
    FarmerRegistrationProfileForm, SupplierRegistrationProfileForm,
    BuyerRegistrationProfileForm, RiderRegistrationProfileForm, RiderVerificationForm
)
from .models import User, VehicleChangeRequest, RiderProfile
import json

def select_role(request):
    """Display role selection page"""
    return render(request, 'users/select_role.html')

def register(request):
    # Determine role from POST data or GET parameter
    role = request.POST.get('role') or request.GET.get('role')
    
    # Initialize profile form to None
    profile_form = None

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        # Instantiate the correct profile form based on the role selected in the main form
        # We need to get the role from the form data to be sure
        if role == User.Role.FARMER:
            profile_form = FarmerRegistrationProfileForm(request.POST)
        elif role == User.Role.SUPPLIER:
            profile_form = SupplierRegistrationProfileForm(request.POST)
        elif role == User.Role.RIDER:
            profile_form = RiderRegistrationProfileForm(request.POST)
        elif role == User.Role.BUYER:
            profile_form = BuyerRegistrationProfileForm(request.POST)

        # Check validity of both forms (if profile_form exists)
        if form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user = form.save(commit=False)
            # Ensure the role matches what we handled (form.cleaned_data['role'] should match 'role' if form is valid)
            user.save()
            
            # Save profile data if we have a form
            if profile_form:
                # The signal creates a profile, so we need to update it
                profile = user.profile
                # Loop through cleaned fields and update profile
                # Loop through cleaned fields and update profile
                for field, value in profile_form.cleaned_data.items():
                    if hasattr(profile, field):
                        setattr(profile, field, value)
                profile.save()
                
                # Handle Rider Specifics
                if role == User.Role.RIDER:
                    try:
                        rider_profile = user.rider_profile
                        if 'vehicle_type' in profile_form.cleaned_data:
                            rider_profile.vehicle_type = profile_form.cleaned_data['vehicle_type']
                        if 'license_plate' in profile_form.cleaned_data:
                            rider_profile.license_plate = profile_form.cleaned_data['license_plate']
                            # Note: rider_profile model field is 'vehicle_plate_number', form is 'license_plate'. Mapping needed.
                            rider_profile.vehicle_plate_number = profile_form.cleaned_data['license_plate']
                        rider_profile.save()
                    except Exception as e:
                        # Log error but don't fail registration completely if profile exists
                        pass

            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('dashboard')
        else:
            # DEBUG: Print errors
            print("Register Form Errors:", form.errors)
            if profile_form:
                print("Profile Form Errors:", profile_form.errors)
                # Add generic error message
                messages.error(request, f"Please correct the errors below. {form.errors if form.errors else ''} {profile_form.errors if profile_form.errors else ''}")
            else:
                 messages.error(request, f"Please correct the errors below. {form.errors}")
    else:
        # GET request
        initial_data = {}
        if role and role in dict(User.Role.choices):
            initial_data['role'] = role
            
            # Pre-instantiate the correct profile form to show fields
            if role == User.Role.FARMER:
                profile_form = FarmerRegistrationProfileForm()
            elif role == User.Role.SUPPLIER:
                profile_form = SupplierRegistrationProfileForm()
            elif role == User.Role.RIDER:
                profile_form = RiderRegistrationProfileForm()
            elif role == User.Role.BUYER:
                profile_form = BuyerRegistrationProfileForm()
                
        form = RegisterForm(initial=initial_data)

    return render(request, 'users/register.html', {
        'form': form,
        'profile_form': profile_form,
        'role': role
    })

@login_required
def dashboard(request):
    user = request.user
    if user.role == User.Role.FARMER:
        # Get orders for products owned by this farmer
        from marketplace.models import Order, Product
        from django.db.models import Sum
        
        # Stats
        orders_count = Order.objects.filter(product__seller=user).count()
        active_products_count = Product.objects.filter(seller=user, available=True).count()
        
        # Order Lists
        pending_orders = Order.objects.filter(product__seller=user, status='PENDING').order_by('-created_at')
        accepted_statuses = ['ACCEPTED', 'ESCROW', 'IN_DELIVERY', 'DELIVERED', 'PAID_OUT', 'COMPLETED']
        accepted_orders = Order.objects.filter(product__seller=user, status__in=accepted_statuses).order_by('-created_at')
        
        # Calculate earnings
        total_earnings = Order.objects.filter(product__seller=user, status='PAID_OUT').aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        context = {
            'orders_count': orders_count,
            'active_products_count': active_products_count,
            'pending_orders': pending_orders,
            'accepted_orders': accepted_orders,
            'total_earnings': total_earnings,
        }
        return render(request, 'users/dashboard_farmer.html', context)
    elif user.role == User.Role.BUYER:
        from marketplace.models import Order, CartItem
        
        # Get buyer stats
        orders = Order.objects.filter(buyer=user).order_by('-created_at')
        recent_orders = orders[:5]
        total_orders = orders.count()
        pending_orders_count = orders.filter(status='PENDING').count()
        cart_item_count = CartItem.objects.filter(buyer=user).count()
        
        context = {
            'recent_orders': recent_orders,
            'total_orders': total_orders,
            'pending_orders_count': pending_orders_count,
            'cart_item_count': cart_item_count,
        }
        return render(request, 'users/dashboard_buyer.html', context)
    elif user.role == User.Role.SUPPLIER:
        return render(request, 'users/dashboard_supplier.html')
    elif user.role == User.Role.RIDER:
        from marketplace.models import Order
        from django.db.models import Sum
        from math import radians, cos, sin, asin, sqrt

        def haversine(lon1, lat1, lon2, lat2):
            """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)
            """
            if not all([lon1, lat1, lon2, lat2]):
                return None
            # convert decimal degrees to radians 
            lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
            # haversine formula 
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            r = 6371 # Radius of earth in kilometers
            return c * r

        # Get rider profile and stats
        rider_profile = user.rider_profile
        rider_lat = rider_profile.current_latitude or user.profile.latitude
        rider_lon = rider_profile.current_longitude or user.profile.longitude
        
        # 1. Available Deliveries (Ready for pickup + Unassigned)
        available_orders_qs = Order.objects.filter(
            is_ready_for_pickup=True,
            assigned_rider__isnull=True,
            status__in=['ACCEPTED', 'ESCROW'] 
        ).order_by('-updated_at')
        
        # Annotate with distance
        available_orders = []
        for order in available_orders_qs:
            seller_profile = order.product.seller.profile
            dist = None
            if rider_lat and rider_lon and seller_profile.latitude and seller_profile.longitude:
                dist = haversine(rider_lon, rider_lat, seller_profile.longitude, seller_profile.latitude)
            
            # Add attributes dynamically for template
            order.distance_km = round(dist, 1) if dist is not None else "N/A"
            order.estimated_fee = int(order.total_price * 0.15) # Mock 15% delivery fee
            available_orders.append(order)

        # 2. Accepted Deliveries (Active Jobs)
        active_deliveries = Order.objects.filter(
            assigned_rider=user,
            status__in=['ACCEPTED', 'ESCROW', 'IN_DELIVERY', 'PICKED_UP'] 
        ).order_by('-updated_at')
        
        # 3. Earnings & History
        completed_orders = Order.objects.filter(assigned_rider=user, status='DELIVERED')
        total_delivered_value = completed_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_earnings = int(total_delivered_value * Decimal('0.15')) # Estimated earnings
        
        delivery_history = completed_orders.order_by('-updated_at')[:10]
        
        # 4. Notifications
        notifications = user.notifications.filter(is_read=False).order_by('-created_at')[:5]

        context = {
            'rider_profile': rider_profile,
            'available_orders': available_orders,
            'active_deliveries': active_deliveries,
            'total_earnings': total_earnings, 
            'delivery_history': delivery_history,
            'notifications': notifications,
        }
        return render(request, 'users/dashboard_rider.html', context)
    else:
        return render(request, 'users/dashboard_base.html') # Fallback

@login_required
def accept_delivery(request, order_id):
    """Rider accepts a delivery"""
    from marketplace.models import Order, Notification
    
    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        # Check Verification Status
        rider_profile = getattr(request.user, 'rider_profile', None)
        if not rider_profile or rider_profile.verification_status != 'VERIFIED':
            messages.error(request, "Access Denied: You must be a VERIFIED rider to accept orders. Please complete your profile verification.")
            return redirect('dashboard')
            
        if not rider_profile.is_available:
            messages.error(request, "You are currently marked as unavailable. Please go online to accept jobs.")
            return redirect('dashboard')

        order = Order.objects.get(id=order_id)
        if order.assigned_rider is None:
            order.assigned_rider = request.user
            # Update status to indicate rider attached, though it might still be waiting for pickup
            # If status was ESCROW/ACCEPTED, maybe keep it or move to specialized state?
            # Let's keep status field as main tracker. 
            # If it was 'ESCROW', it implies paid. 
            
            order.save()
            
            messages.success(request, f"You have accepted order #{order.id}")
            
            # Notify Farmer
            Notification.objects.create(
                user=order.product.seller,
                notification_type='ORDER_ASSIGNED',
                order=order,
                message=f"Rider {request.user.username} has accepted your delivery request for {order.product.name}."
            )
            
            # Notify Buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='ORDER_ASSIGNED',
                order=order,
                message=f"Rider {request.user.username} is on the way to pick up your order."
            )
            
        else:
            messages.error(request, "This order has already been taken.")
            
    return redirect('dashboard')

@login_required
def update_delivery_status(request, order_id):
    """Rider updates status (Picked Up, Delivered)"""
    from marketplace.models import Order, Notification
    
    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        order = Order.objects.get(id=order_id)
        action = request.POST.get('action')
        
        if order.assigned_rider != request.user:
            messages.error(request, "Not authorized")
            return redirect('dashboard')
            
        if action == 'picked_up':
            order.status = 'IN_DELIVERY'
            order.save()
            messages.success(request, "Order marked as Picked Up")
            # Notify Buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='ORDER_UPDATED', # Add this type if strict or use accepted
                order=order,
                message=f"Your order for {order.product.name} has been picked up and is on the way!"
            )
            
        elif action == 'delivered':
            order.status = 'DELIVERED'
            request.user.rider_profile.completed_deliveries += 1
            request.user.rider_profile.total_deliveries += 1
            request.user.rider_profile.save()
            order.save()
            messages.success(request, "Order marked as Delivered")
             # Notify Farmer to confirm/get paid
            Notification.objects.create(
                user=order.product.seller,
                notification_type='ORDER_UPDATED',
                order=order,
                message=f"Order #{order.id} has been delivered. Funds will be released shortly."
            )
            
    return redirect('dashboard')

@login_required
def reject_delivery(request, order_id):
    """Rider rejects a delivery request"""
    from marketplace.models import Order, Notification
    
    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        order = get_object_or_404(Order, id=order_id)
        
        # Only allow rejection if order is not yet assigned
        if order.assigned_rider is None and order.is_ready_for_pickup:
            # Notify Farmer
            Notification.objects.create(
                user=order.product.seller,
                notification_type='ORDER_UPDATED',
                order=order,
                message=f"Rider {request.user.username} declined your delivery request for {order.product.name}. Please find another rider."
            )
            
            messages.info(request, f"You have declined order #{order.id}")
        else:
            messages.error(request, "This order cannot be rejected at this time.")
            
    return redirect('dashboard')



@login_required
def view_profile(request, username):
    """Dispatcher view for public profiles based on role"""
    target_user = get_object_or_404(User, username=username)
    
    if target_user.role == User.Role.RIDER:
        return view_rider_profile(request, username)
        
    # Default/Generic Profile View
    is_own_profile = (request.user == target_user)
    context = {
        'profile_user': target_user,
        'is_own_profile': is_own_profile,
    }
    return render(request, 'users/profile_display.html', context)

@login_required
def view_rider_profile(request, username):
    rider_user = get_object_or_404(User, username=username, role=User.Role.RIDER)
    is_own_profile = (request.user == rider_user)
    
    # Get reviews
    reviews = rider_user.rider_reviews.all().order_by('-created_at')
    
    # Calculate average rating
    from django.db.models import Avg
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Active deliveries for public view might be sensitive, maybe just count?
    active_deliveries = rider_user.assigned_orders.filter(status__in=['ACCEPTED', 'ESCROW', 'IN_DELIVERY']).count()
    
    # Recent deliveries (completed)
    recent_deliveries = rider_user.assigned_orders.filter(status='DELIVERED').order_by('-updated_at')[:5]

    context = {
        'profile_user': rider_user,
        'is_own_profile': is_own_profile,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'active_deliveries': active_deliveries,
        'recent_deliveries': recent_deliveries,
    }
    return render(request, 'users/profile_rider.html', context)

@login_required
def rider_profile_edit(request):
    """Edit Rider Profile and Upload Docs"""
    # Simply reuse the main edit_profile or specialized?
    # Let's use the main one but ensure the template shows rider fields
    # Or creating a new view if specialized handling needed for 5 images.
    
    # For now, rely on existing edit_profile logic but ensure forms are correct.
    # The existing edit_profile uses ProfileUpdateForm which is for standard Profile model.
    # Rider info is in RiderProfile.
    
    if request.method == 'POST':
        user = request.user
        # Retrieve images manually or via a Form
        rider_profile = user.rider_profile
        
        vehicle_type = request.POST.get('vehicle_type')
        plate = request.POST.get('vehicle_plate_number')
        id_num = request.POST.get('id_number')
        lic_num = request.POST.get('license_number')
        phone = request.POST.get('phone_number') # Get phone
        
        if vehicle_type: rider_profile.vehicle_type = vehicle_type
        if plate: rider_profile.vehicle_plate_number = plate
        if id_num: rider_profile.id_number = id_num
        if lic_num: rider_profile.license_number = lic_num
        
        # Update Phone Number (on Profile model)
        if phone:
            profile = user.profile
            profile.phone_number = phone
            profile.save()
        
        # Handle images
        if request.FILES.get('passport_photo'):
            rider_profile.passport_photo = request.FILES['passport_photo']
        if request.FILES.get('verification_id_front'):
            rider_profile.verification_id_front = request.FILES['verification_id_front']
        if request.FILES.get('verification_id_back'):
            rider_profile.verification_id_back = request.FILES['verification_id_back']
        if request.FILES.get('verification_selfie'):
            rider_profile.verification_selfie = request.FILES['verification_selfie']
        if request.FILES.get('verification_license'):
            rider_profile.verification_license = request.FILES['verification_license']
        if request.FILES.get('verification_good_conduct'):
            rider_profile.verification_good_conduct = request.FILES['verification_good_conduct']
            
        rider_profile.save()
        messages.success(request, "Rider profile updated")
        return redirect('profile') # Which redirects to public_profile
        
    return render(request, 'users/profile_rider_edit.html', {'user': request.user})

@login_required
def add_rider_review(request, rider_id):
    if request.method == 'POST':
        from .models import RiderReview
        rider_user = get_object_or_404(User, id=rider_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            RiderReview.objects.create(
                rider=rider_user,
                reviewer=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review submitted successfully!')
        else:
            messages.error(request, 'Please provide both a rating and a comment.')
            
        return redirect('view_rider_profile', username=rider_user.username)
    return redirect('dashboard')


@login_required
def profile(request):
    """Display user profile"""
    # Delegate to the comprehensive public_profile view which handles all roles (Rider, Farmer, Buyer)
    # and properly loads context like badges, reviews, and stats.
    return public_profile(request, request.user.id)

@login_required
def edit_profile(request):
    """Handle profile updates"""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile_edit.html', context)

@login_required
def update_profile_photo(request):
    """Handle AJAX photo upload from camera or gallery"""
    from django.http import JsonResponse
    
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            profile = request.user.profile
            profile.avatar = request.FILES['avatar']
            profile.save()
            
            return JsonResponse({
                'success': True,
                'avatar_url': profile.avatar.url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'No photo provided'
    }, status=400)

@login_required
def profile(request):
    """View own profile - redirects to public_profile with own user_id"""
    return public_profile(request, request.user.id)

def public_profile(request, user_id):
    """View any user's public profile (especially for riders)"""
    from django.shortcuts import get_object_or_404
    from .models import Review, FavoriteFarmer
    from marketplace.models import Product, Order
    from django.db.models import Avg

    profile_user = get_object_or_404(User, id=user_id)
    is_own_profile = request.user.is_authenticated and request.user.id == user_id
    
    # Get reviews
    # Get reviews based on role
    if profile_user.role == User.Role.FARMER:
        from .review_models import FarmerReview
        raw_reviews = FarmerReview.objects.filter(farmer=profile_user).select_related('buyer', 'buyer__profile').order_by('-created_at')
        # Calculate avg rating before list conversion
        avg_rating = raw_reviews.aggregate(Avg('rating'))['rating__avg']
        
        # Adapt fields for generic template (profile_display.html expects reviewer and comment)
        reviews = []
        for r in raw_reviews:
            r.reviewer = r.buyer
            r.comment = r.review_text
            reviews.append(r)
    else:
        reviews = Review.objects.filter(reviewed_user=profile_user).order_by('-created_at')
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    if avg_rating:
        avg_rating = round(avg_rating, 1)
    
    # Check if favorited
    is_favorited = False
    if request.user.is_authenticated and request.user != profile_user:
        is_favorited = FavoriteFarmer.objects.filter(buyer=request.user, farmer=profile_user).exists()

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': len(reviews),
        'is_favorited': is_favorited,
    }

    # For riders, use the rider-specific template with stats
    if profile_user.role == 'RIDER':
        # Calculate stats dynamically if not in model or to augment
        assigned_orders = Order.objects.filter(assigned_rider=profile_user)
        
        # We can also trust the model stats if updated via signals, but dynamic is fresher
        completed_deliveries = assigned_orders.filter(status='DELIVERED').count()
        active_deliveries = assigned_orders.filter(status__in=['ACCEPTED', 'IN_DELIVERY', 'PICKED_UP']).count()
        recent_deliveries = assigned_orders.order_by('-updated_at')[:5]
        
        context.update({
            'completed_deliveries': completed_deliveries,
            'active_deliveries': active_deliveries,
            'recent_deliveries': recent_deliveries,
        })
        return render(request, 'users/profile_rider.html', context)
    
    # For buyers, use buyer-specific template with delivery addresses
    if profile_user.role == 'BUYER':
        from .models import DeliveryAddress
        delivery_addresses = DeliveryAddress.objects.filter(user=profile_user)
        total_orders = Order.objects.filter(buyer=profile_user).count()
        
        context.update({
            'delivery_addresses': delivery_addresses,
            'total_orders': total_orders,
        })
        return render(request, 'users/profile_buyer.html', context)
    
    # For other roles (Farmer/Supplier), use default profile display
    products = Product.objects.filter(seller=profile_user, available=True)
    context['products'] = products
    
    # Add farmer badge data if user is a farmer
    if profile_user.role == 'FARMER':
        from .review_models import FarmerBadge
        farmer_badge, created = FarmerBadge.objects.get_or_create(farmer=profile_user)
        if not created:
            farmer_badge.update_badge_level()
        
        # Define badge requirements for progress tracking
        badge_tiers = {
            'BEGINNER': {'name': 'Beginner', 'icon': '🌱', 'sales': 0, 'rating': 0.0, 'reviews': 0},
            'BRONZE': {'name': 'Bronze', 'icon': '🥉', 'sales': 25, 'rating': 3.0, 'reviews': 5},
            'SILVER': {'name': 'Silver', 'icon': '🥈', 'sales': 100, 'rating': 3.5, 'reviews': 15},
            'GOLD': {'name': 'Gold', 'icon': '🥇', 'sales': 250, 'rating': 4.0, 'reviews': 50},
            'PLATINUM': {'name': 'Platinum', 'icon': '💎', 'sales': 500, 'rating': 4.5, 'reviews': 100},
            'DIAMOND': {'name': 'Diamond', 'icon': '💠', 'sales': 1000, 'rating': 4.8, 'reviews': 200},
        }
        
        # Determine next badge level
        tier_order = ['BEGINNER', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND']
        current_index = tier_order.index(farmer_badge.badge_level)
        next_badge = None
        if current_index < len(tier_order) - 1:
            next_badge_level = tier_order[current_index + 1]
            next_badge = badge_tiers[next_badge_level]
        
        context.update({
            'farmer_badge': farmer_badge,
            'badge_tiers': badge_tiers,
            'next_badge': next_badge,
        })
    
    return render(request, 'users/profile_display.html', context)

@login_required
def delete_account(request):
    """Delete user account permanently"""
    if request.method == 'POST':
        user = request.user
        # Log out the user first
        from django.contrib.auth import logout
        logout(request)
        # Delete the user account (this will cascade delete related data)
        user.delete()
        # Add success message
        messages.success(request, 'Your account has been successfully deleted.')
        # Redirect to landing page
        return redirect('landing_page')
    # If not POST, redirect to profile
    return redirect('profile')

@login_required
def add_delivery_address(request):
    """Add a new delivery address"""
    if request.method == 'POST':
        from .models import DeliveryAddress
        
        address = DeliveryAddress.objects.create(
            user=request.user,
            label=request.POST.get('label', ''),
            county=request.POST.get('county'),
            constituency=request.POST.get('constituency'),
            ward=request.POST.get('ward'),
            gps_coordinates=request.POST.get('gps_coordinates', ''),
            additional_details=request.POST.get('additional_details', ''),
            is_default=request.POST.get('is_default') == 'on'
        )
        messages.success(request, 'Delivery address added successfully!')
    return redirect('profile')

@login_required
def edit_delivery_address(request, address_id):
    """Edit an existing delivery address"""
    if request.method == 'POST':
        from .models import DeliveryAddress
        address = get_object_or_404(DeliveryAddress, id=address_id, user=request.user)
        
        address.label = request.POST.get('label', '')
        address.county = request.POST.get('county')
        address.constituency = request.POST.get('constituency')
        address.ward = request.POST.get('ward')
        address.gps_coordinates = request.POST.get('gps_coordinates', '')
        address.additional_details = request.POST.get('additional_details', '')
        
        if request.POST.get('is_default') == 'on':
            address.is_default = True
            
        address.save()
        messages.success(request, 'Delivery address updated successfully!')
    return redirect('profile')

@login_required
def set_default_address(request, address_id):
    """Set an address as default"""
    if request.method == 'POST':
        from .models import DeliveryAddress
        address = DeliveryAddress.objects.filter(id=address_id, user=request.user).first()
        if address:
            address.is_default = True
            address.save()
            messages.success(request, 'Default address updated!')
    return redirect('profile')

@login_required
def delete_address(request, address_id):
    """Delete a delivery address"""
    if request.method == 'POST':
        from .models import DeliveryAddress
        address = DeliveryAddress.objects.filter(id=address_id, user=request.user).first()
        if address and not address.is_default:
            address.delete()
            messages.success(request, 'Address deleted successfully!')
        elif address and address.is_default:
            messages.error(request, 'Cannot delete default address. Set another address as default first.')
    return redirect('profile')


@login_required
def farmer_profile_public(request, farmer_id):
    """Public profile view for farmers - visible to buyers"""
    from django.shortcuts import get_object_or_404
    from django.db.models import Avg
    from django.db import models
    from .review_models import FarmerReview, FarmerBadge
    from .review_forms import FarmerReviewForm
    from marketplace.models import Product
    
    farmer = get_object_or_404(User, id=farmer_id, role=User.Role.FARMER)
    
    # Get or create farmer badge
    farmer_badge, created = FarmerBadge.objects.get_or_create(farmer=farmer)
    if not created:
        farmer_badge.update_badge_level()
    
    # Get farmer's products
    products = Product.objects.filter(seller=farmer, available=True)[:6]
    
    # Get reviews
    reviews = FarmerReview.objects.filter(farmer=farmer).select_related('buyer', 'buyer__profile')
    
    # Calculate rating stats
    rating_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=models.Count('id')
    )
    
    # Check if current user has already reviewed
    user_review = None
    can_review = False
    is_favorite = False
    
    if request.user.is_authenticated and request.user.role == User.Role.BUYER:
        user_review = reviews.filter(buyer=request.user).first()
        can_review = user_review is None
        is_favorite = request.user.profile.favorite_farmers.filter(id=farmer.id).exists()
    
    # Review form
    review_form = FarmerReviewForm() if can_review else None
    
    context = {
        'farmer': farmer,
        'farmer_profile': farmer.profile,
        'farmer_badge': farmer_badge,
        'products': products,
        'reviews': reviews,
        'rating_stats': rating_stats,
        'user_review': user_review,
        'can_review': can_review,
        'is_favorite': is_favorite,
        'review_form': review_form,
    }
    
    return render(request, 'users/farmer_profile_public.html', context)


@login_required
def submit_review(request, farmer_id):
    """Submit or update a review for a farmer"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from .review_models import FarmerReview, FarmerBadge
    from .review_forms import FarmerReviewForm
    
    if request.user.role != User.Role.BUYER:
        messages.error(request, 'Only buyers can submit reviews.')
        return redirect('farmer_profile_public', farmer_id=farmer_id)
    
    farmer = get_object_or_404(User, id=farmer_id, role=User.Role.FARMER)
    
    if request.method == 'POST':
        # Check if review already exists
        review = FarmerReview.objects.filter(farmer=farmer, buyer=request.user).first()
        
        if review:
            form = FarmerReviewForm(request.POST, instance=review)
        else:
            form = FarmerReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.farmer = farmer
            review.buyer = request.user
            review.save()
            
            # Update farmer badge
            farmer_badge = FarmerBadge.objects.get(farmer=farmer)
            farmer_badge.update_badge_level()
            
            messages.success(request, 'Review submitted successfully!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Review submitted!'})
        else:
            messages.error(request, 'Please correct the errors in your review.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    
    return redirect('farmer_profile_public', farmer_id=farmer_id)


@login_required
def toggle_favorite_farmer(request, farmer_id):
    """Toggle favorite status of a farmer for the current buyer"""
    from django.shortcuts import get_object_or_404
    
    if request.user.role != User.Role.BUYER:
        messages.error(request, 'Only buyers can have favorite farmers.')
        return redirect('dashboard')
        
    farmer = get_object_or_404(User, id=farmer_id, role=User.Role.FARMER)
    profile = request.user.profile
    
    if profile.favorite_farmers.filter(id=farmer_id).exists():
        profile.favorite_farmers.remove(farmer)
        messages.success(request, f'{farmer.username} removed from favorites.')
        is_favorite = False
    else:
        profile.favorite_farmers.add(farmer)
        messages.success(request, f'{farmer.username} added to favorites.')
        is_favorite = True
        
    # Check if this was an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'message': 'Favorites updated'
        })
        
    # Redirect back to where they came from
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def favorite_farmers_list(request):
    """List of favorite farmers for the current buyer"""
    if request.user.role != User.Role.BUYER:
        messages.error(request, 'Only buyers can have favorite farmers.')
        return redirect('dashboard')
        
    favorite_farmers = request.user.profile.favorite_farmers.all().select_related('profile')
    
    context = {
        'favorite_farmers': favorite_farmers
    }
    return render(request, 'users/favorite_farmers.html', context)

@login_required
def toggle_rider_availability(request):
    """Toggle rider availability status"""
    from django.http import JsonResponse
    import json

    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        is_ajax = request.headers.get('content-type') == 'application/json'
        
        try:
            rider_profile = request.user.rider_profile
            
            if is_ajax:
                data = json.loads(request.body)
                target_status = data.get('is_available')
                if target_status is not None:
                     rider_profile.is_available = target_status
                else:
                     rider_profile.is_available = not rider_profile.is_available
            else:
                rider_profile.is_available = not rider_profile.is_available
                
            rider_profile.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'is_available': rider_profile.is_available,
                    'status': "Available" if rider_profile.is_available else "Offline"
                })

            status = "Available" if rider_profile.is_available else "Offline"
            messages.success(request, f"You are now {status}")
        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, "Error updating status")
            
    return redirect('dashboard')

@login_required
def rider_withdraw(request):
    """Handle rider withdrawal requests"""
    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        try:
            amount = float(request.POST.get('amount', 0))
            rider_profile = request.user.rider_profile
            
            if amount <= 0:
                 messages.error(request, "Invalid amount")
            elif amount > rider_profile.wallet_balance:
                 messages.error(request, "Insufficient funds")
            else:
                 # TODO: Integrate M-Pesa B2C
                 rider_profile.wallet_balance -= amount
                 rider_profile.save()
                 messages.success(request, f"Withdrawal request of KES {amount} received. Processing...")
                 
        except ValueError:
             messages.error(request, "Invalid amount format")
        except Exception as e:
             messages.error(request, f"Error processing withdrawal: {str(e)}")
             
    return redirect('dashboard')

@login_required
def update_location(request):
    """Update user's real-time GPS location (Works for Riders and Farmers/Buyers)"""
    if request.method == 'POST' and request.headers.get('content-type') == 'application/json':
        try:
            import json
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude and longitude:
                # Update generic Profile (for Farmers/Buyers)
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    profile.latitude = latitude
                    profile.longitude = longitude
                    profile.save()
                
                # Update RiderProfile if exists (for Riders) - keep specialized fields in sync or use them
                if request.user.role == User.Role.RIDER and hasattr(request.user, 'rider_profile'):
                    rider_profile = request.user.rider_profile
                    rider_profile.current_latitude = latitude
                    rider_profile.current_longitude = longitude
                    rider_profile.save()
                
                return JsonResponse({'status': 'success'})
                
        except Exception as e:
            pass # Silent fail
            
            pass # Silent fail
            
    return JsonResponse({'status': 'error'}, status=400)

def get_locations(request):
    """API to fetch sub-locations (SubCounties or Wards)"""
    parent_type = request.GET.get('parent_type')
    parent_id = request.GET.get('parent_id')
    
    data = []
    
    if parent_type == 'county' and parent_id:
        from .models import SubCounty
        sub_counties = SubCounty.objects.filter(county_id=parent_id).values('id', 'name')
        data = list(sub_counties)
        
    elif parent_type == 'sub_county' and parent_id:
        from .models import Ward
        wards = Ward.objects.filter(sub_county_id=parent_id).values('id', 'name')
        data = list(wards)
        
    from django.http import JsonResponse
    return JsonResponse({'results': data})

# ============= RIDER SETTINGS VIEWS =============

@login_required
def rider_settings(request):
    """Rider settings page"""
    if request.user.role != User.Role.RIDER:
        messages.error(request, "Access denied. Riders only.")
        return redirect('dashboard')
    
    # Check for pending vehicle change requests
    pending_vehicle_request = VehicleChangeRequest.objects.filter(
        rider=request.user,
        status='PENDING'
    ).first()
    
    context = {
        'pending_vehicle_request': pending_vehicle_request,
    }
    return render(request, 'users/rider_settings.html', context)

@login_required
@require_POST
def update_personal_info(request):
    """Update rider personal information"""
    if request.user.role != User.Role.RIDER:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    try:
        # Update User model
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            name_parts = full_name.split(' ', 1)
            request.user.first_name = name_parts[0]
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        
        # Update Profile model
        profile = request.user.profile
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.whatsapp_number = request.POST.get('whatsapp_number', '')
        profile.bio = request.POST.get('bio', '')
        profile.save()
        
        messages.success(request, "Personal information updated successfully!")
        return redirect('rider_settings')
    except Exception as e:
        messages.error(request, f"Error updating information: {str(e)}")
        return redirect('rider_settings')

@login_required
@require_POST
def request_vehicle_change(request):
    """Submit a vehicle change request for admin approval"""
    if request.user.role != User.Role.RIDER:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    # Check if there's already a pending request
    existing_request = VehicleChangeRequest.objects.filter(
        rider=request.user,
        status='PENDING'
    ).exists()
    
    if existing_request:
        messages.warning(request, "You already have a pending vehicle change request.")
        return redirect('rider_settings')
    
    try:
        rider_profile = request.user.rider_profile
        
        # Create change request
        VehicleChangeRequest.objects.create(
            rider=request.user,
            old_vehicle_type=rider_profile.vehicle_type,
            old_vehicle_plate=rider_profile.vehicle_plate_number or '',
            old_license_number=rider_profile.license_number or '',
            new_vehicle_type=request.POST.get('new_vehicle_type'),
            new_vehicle_plate=request.POST.get('new_vehicle_plate'),
            new_license_number=request.POST.get('new_license_number', ''),
            reason=request.POST.get('reason')
        )
        
        messages.success(request, "Vehicle change request submitted! An admin will review it soon.")
        return redirect('rider_settings')
    except Exception as e:
        messages.error(request, f"Error submitting request: {str(e)}")
        return redirect('rider_settings')

@login_required
@require_POST
def update_location_settings(request):
    """Update rider location and service area"""
    if request.user.role != User.Role.RIDER:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    try:
        rider_profile = request.user.rider_profile
        rider_profile.county = request.POST.get('county', '')
        rider_profile.constituency = request.POST.get('constituency', '')
        rider_profile.ward = request.POST.get('ward', '')
        rider_profile.estate_village = request.POST.get('estate_village', '')
        rider_profile.save()
        
        messages.success(request, "Location settings updated successfully!")
        return redirect('rider_settings')
    except Exception as e:
        messages.error(request, f"Error updating location: {str(e)}")
        return redirect('rider_settings')

@login_required
def rider_upload_documents(request):
    if request.user.role != User.Role.RIDER:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    rider_profile = request.user.rider_profile
    
    if request.method == 'POST':
        form = RiderVerificationForm(request.POST, request.FILES, instance=rider_profile)
        if form.is_valid():
            form.save(commit=False)
            rider_profile = form.save()
            
            # Update status to PENDING whenever new docs are uploaded
            rider_profile.verification_status = 'PENDING'
            rider_profile.save()
            
            messages.success(request, "Documents uploaded successfully! Status updated to Pending Verification.")
            return redirect('dashboard')
    else:
        form = RiderVerificationForm(instance=rider_profile)
    
    return render(request, 'users/rider_upload_documents.html', {'form': form})

# --- Admin Verification Views ---

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_rider_verification_list(request):
    # Get all riders, prioritize pending ones
    pending_riders = RiderProfile.objects.filter(verification_status='PENDING').order_by('-user__date_joined')
    other_riders = RiderProfile.objects.exclude(verification_status='PENDING').order_by('-user__date_joined')
    
    context = {
        'pending_riders': pending_riders,
        'other_riders': other_riders,
    }
    return render(request, 'users/admin_rider_verification_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_rider_verification_detail(request, rider_id):
    rider_profile = get_object_or_404(RiderProfile, id=rider_id)
    return render(request, 'users/admin_rider_verification_detail.html', {'rider_profile': rider_profile})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_rider_verification_action(request, rider_id):
    if request.method != 'POST':
        return redirect('admin_rider_verification_detail', rider_id=rider_id)
        
    rider_profile = get_object_or_404(RiderProfile, id=rider_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        rider_profile.verification_status = 'VERIFIED'
        rider_profile.save()
        messages.success(request, f'Rider {rider_profile.user.username} has been verified.')
    elif action == 'reject':
        rider_profile.verification_status = 'REJECTED'
        rider_profile.save()
        messages.warning(request, f'Rider {rider_profile.user.username} verification rejected.')
        
    return redirect('admin_rider_verification_list')

