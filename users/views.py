from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm,
    FarmerRegistrationProfileForm, SupplierRegistrationProfileForm,
    BuyerRegistrationProfileForm, RiderRegistrationProfileForm
)
from .models import User

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
        from marketplace.models import Order
        orders_count = Order.objects.filter(product__seller=user).count()
        pending_orders = Order.objects.filter(product__seller=user, status='PENDING').order_by('-created_at')
        accepted_orders = Order.objects.filter(product__seller=user, status__in=['ACCEPTED', 'ESCROW']).order_by('-created_at')
        context = {
            'orders_count': orders_count,
            'pending_orders': pending_orders,
            'accepted_orders': accepted_orders,
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
        
        # Get rider profile and stats
        rider_profile = user.rider_profile
        assigned_orders = Order.objects.filter(assigned_rider=user)
        
        active_deliveries = assigned_orders.filter(status__in=['ACCEPTED', 'IN_DELIVERY', 'PICKED_UP'])
        
        context = {
            'rider_profile': rider_profile,
            'assigned_orders': assigned_orders.order_by('-updated_at'),
            'active_deliveries': active_deliveries,
        }
        return render(request, 'users/dashboard_rider.html', context)
    else:
        return render(request, 'users/dashboard_base.html') # Fallback

@login_required
def profile(request):
    """Display user profile with posts and products"""
    user = request.user
    posts = user.posts.all()
    products = user.products.all()
    
    # If rider, route to public_profile view with is_own_profile flag
    if user.role == 'RIDER':
        return public_profile(request, user.id)
    
    context = {
        'user': user,
        'posts': posts,
        'products': products,
        'is_own_profile': True
    }
    return render(request, 'users/profile_display.html', context)

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
        'review_count': reviews.count(),
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
    if request.method == 'POST' and request.user.role == User.Role.RIDER:
        try:
            rider_profile = request.user.rider_profile
            rider_profile.is_available = not rider_profile.is_available
            rider_profile.save()
            status = "Available" if rider_profile.is_available else "Offline"
            messages.success(request, f"You are now {status}")
        except Exception as e:
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
def update_rider_location(request):
    """Update rider's real-time GPS location"""
    if request.method == 'POST' and request.headers.get('content-type') == 'application/json':
        try:
            import json
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude and longitude and request.user.role == User.Role.RIDER:
                rider_profile = request.user.rider_profile
                rider_profile.current_latitude = latitude
                rider_profile.current_longitude = longitude
                rider_profile.save()
                
                from django.http import JsonResponse
                return JsonResponse({'status': 'success'})
                
        except Exception as e:
            pass # Silent fail for background updates
            
    from django.http import JsonResponse
    return JsonResponse({'status': 'error'}, status=400)
