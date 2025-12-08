#!/usr/bin/env python
# Script to fix corrupted users/views.py file

import os

# Read the file
with open('users/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep only the first 294 lines (the clean part)
clean_lines = lines[:294]

# Add the missing functions
missing_functions = '''
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')
    return render(request, 'users/delete_account.html')

def public_profile(request, user_id):
    """Display a role-specific public profile for any user"""
    from .models import Review, FavoriteFarmer
    from marketplace.models import Product, Order
    
    profile_user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(reviewed_user=profile_user).order_by('-created_at')
    
    # Check if current user has favorited this user
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = FavoriteFarmer.objects.filter(
            buyer=request.user, 
            farmer=profile_user
        ).exists()
    
    # Base context
    context = {
        'profile_user': profile_user,
        'reviews': reviews,
        'is_own_profile': request.user == profile_user,
        'is_favorited': is_favorited
    }
    
    # Role-specific data and templates
    if profile_user.role == 'RIDER':
        # Rider-specific data
        assigned_orders = Order.objects.filter(assigned_rider=profile_user)
        completed_deliveries = assigned_orders.filter(status='DELIVERED').count()
        active_deliveries = assigned_orders.filter(status__in=['ACCEPTED', 'IN_DELIVERY']).count()
        recent_deliveries = assigned_orders.order_by('-created_at')[:5]
        
        context.update({
            'completed_deliveries': completed_deliveries,
            'active_deliveries': active_deliveries,
            'recent_deliveries': recent_deliveries,
        })
        return render(request, 'users/profile_rider.html', context)
    
    else:
        # Farmer/Supplier profile (default)
        products = Product.objects.filter(seller=profile_user, available=True)
        context['products'] = products
        return render(request, 'users/profile_display.html', context)

@login_required
def add_review(request, user_id):
    """Add a review for a farmer/supplier/rider"""
    from .models import Review
    
    if request.method == 'POST':
        reviewed_user = get_object_or_404(User, id=user_id)
        
        # Prevent self-review
        if request.user == reviewed_user:
            messages.error(request, "You cannot review yourself!")
            return redirect('public_profile', user_id=user_id)
        
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        # Create or update review
        review, created = Review.objects.update_or_create(
            reviewer=request.user,
            reviewed_user=reviewed_user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        # Update average rating
        reviews = Review.objects.filter(reviewed_user=reviewed_user)
        avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
        reviewed_user.profile.average_rating = round(avg_rating, 2)
        reviewed_user.profile.total_reviews = reviews.count()
        reviewed_user.profile.save()
        
        messages.success(request, "Review submitted successfully!")
        return redirect('public_profile', user_id=user_id)
    
    return redirect('public_profile', user_id=user_id)

@login_required
def toggle_favorite(request, user_id):
    """Toggle favorite status for a farmer"""
    from .models import FavoriteFarmer
    from django.http import JsonResponse
    
    if request.method == 'POST':
        farmer = get_object_or_404(User, id=user_id)
        
        favorite, created = FavoriteFarmer.objects.get_or_create(
            buyer=request.user,
            farmer=farmer
        )
        
        if not created:
            favorite.delete()
            favorited = False
        else:
            favorited = True
        
        return JsonResponse({'favorited': favorited})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
'''

# Write the fixed file
with open('users/views.py', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
    f.write(missing_functions)

print("✅ File fixed successfully!")
print(f"Original lines: {len(lines)}")
print(f"New lines: {len(clean_lines) + len(missing_functions.split(chr(10)))}")
