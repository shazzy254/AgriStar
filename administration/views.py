from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from users.models import User, Profile
from marketplace.models import Product, Order

def is_admin(user):
    return user.is_authenticated and user.role == User.Role.ADMIN

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Analytics
    total_users = User.objects.count()
    total_farmers = User.objects.filter(role=User.Role.FARMER).count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='COMPLETED').aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Recent Activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Pending Approvals
    pending_products = Product.objects.filter(approval_status='PENDING').count()
    
    context = {
        'total_users': total_users,
        'total_farmers': total_farmers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
        'recent_orders': recent_orders,
        'pending_products': pending_products,
    }
    return render(request, 'administration/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    return render(request, 'administration/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def verify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if hasattr(user, 'profile'):
        user.profile.is_verified = True
        user.profile.save()
        messages.success(request, f'User {user.username} verified successfully.')
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def suspend_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = 'activated' if user.is_active else 'suspended'
    messages.success(request, f'User {user.username} {status} successfully.')
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def product_approval(request):
    pending_products = Product.objects.filter(approval_status='PENDING').select_related('seller')
    return render(request, 'administration/product_approval.html', {'products': pending_products})

@login_required
@user_passes_test(is_admin)
def approve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.approval_status = 'APPROVED'
    product.save()
    messages.success(request, f'Product {product.name} approved.')
    return redirect('admin_product_approval')

@login_required
@user_passes_test(is_admin)
def reject_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.approval_status = 'REJECTED'
    product.save()
    messages.warning(request, f'Product {product.name} rejected.')
    return redirect('admin_product_approval')
