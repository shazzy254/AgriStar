from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm
from .models import User

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    if user.role == User.Role.FARMER:
        # Get orders for products owned by this farmer
        from marketplace.models import Order
        orders_count = Order.objects.filter(product__seller=user).count()
        pending_orders = Order.objects.filter(product__seller=user, status='PENDING').order_by('-created_at')
        context = {
            'orders_count': orders_count,
            'pending_orders': pending_orders,
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
    else:
        return render(request, 'users/dashboard_base.html') # Fallback

@login_required
def profile(request):
    """Display user profile with posts and products"""
    user = request.user
    posts = user.posts.all()
    products = user.products.all()
    
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

