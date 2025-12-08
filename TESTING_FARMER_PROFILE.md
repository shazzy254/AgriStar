# Testing Guide: Farmer Profile "Add Product" Feature

## Overview
This guide will help you test the new "Sell Product" and "Add New Product" buttons that have been added to the farmer profile pages.

## What Was Implemented

### 1. Profile Page (profile.html)
- **Location**: `/users/profile/`
- **Button 1**: "Add Product" button in the header (next to "Edit Profile")
- **Button 2**: "Add New Product" button above the products grid
- **Button 3**: "List Your First Product" button (shown when no products exist)

### 2. Profile Display Page (profile_display.html)
- **Location**: `/users/profile/` and `/users/profile/<user_id>/`
- **Button 1**: "Sell Product" button in header (only visible to farmers viewing their own profile)
- **Button 2**: "Add New Product" button above products grid (only visible to farmers viewing their own profile)

## Testing Steps

### Step 1: Login as a Farmer
1. Navigate to: `http://localhost:8000/users/login/`
2. Login with a farmer account
   - If you don't have one, register at: `http://localhost:8000/users/register/`
   - Select "Farmer" as the role

### Step 2: Navigate to Your Profile
1. Click on "Profile" in the navigation menu
2. You should be redirected to: `http://localhost:8000/users/profile/`

### Step 3: Verify the Buttons Appear
Look for these buttons on your profile page:

#### In the Header Section (below your name and location):
- ✅ "Edit Profile" button (white/light colored)
- ✅ "Add Product" or "Sell Product" button (green, with a plus icon)

#### Above the Products Grid:
- ✅ "Add New Product" button (green, rounded pill style)

#### If You Have No Products:
- ✅ "List Your First Product" button (in the center of the empty products area)

### Step 4: Test Button Functionality
1. Click on any of the "Add Product" / "Sell Product" / "Add New Product" buttons
2. You should be redirected to: `http://localhost:8000/marketplace/create/`
3. This is the product creation form where you can add a new product

### Step 5: Test Product Creation (Optional)
1. Fill in the product form:
   - Product Name
   - Description
   - Price
   - Unit (e.g., kg, piece, bunch)
   - Category
   - Upload an image (optional)
2. Click "Submit" or "Create Product"
3. You should be redirected back to the marketplace
4. Navigate back to your profile to see the new product listed

### Step 6: Verify Public Profile View
1. While logged in as a farmer, visit another user's profile: `http://localhost:8000/users/profile/<other_user_id>/`
2. Verify that you do NOT see the "Sell Product" or "Add New Product" buttons on their profile
3. These buttons should only appear on YOUR OWN profile

## Expected Behavior

### For Farmers Viewing Their Own Profile:
- ✅ See "Edit Profile" button
- ✅ See "Sell Product" button (green)
- ✅ See "Add New Product" button above products
- ✅ All buttons redirect to product creation page

### For Farmers Viewing Other Profiles:
- ✅ See contact buttons (Call, WhatsApp, Write Review)
- ❌ Do NOT see "Sell Product" button
- ❌ Do NOT see "Add New Product" button

### For Non-Farmers (Buyers, Suppliers, Riders):
- ❌ Do NOT see "Sell Product" button on their own profile
- ✅ May see other role-specific buttons

## Troubleshooting

### Issue: Buttons Not Appearing
**Solution**: 
- Verify you're logged in as a FARMER
- Check that you're on YOUR OWN profile page
- Clear browser cache and refresh

### Issue: "NoReverseMatch" Error
**Solution**: 
- This means the URL 'create_product' is not found
- Verify marketplace URLs are properly configured
- Check that `marketplace/urls.py` has: `path('create/', views.create_product, name='create_product')`

### Issue: 404 Error When Clicking Button
**Solution**:
- Verify the `create_product` view exists in `marketplace/views.py`
- Check that the marketplace app is included in main `urls.py`

### Issue: Permission Denied
**Solution**:
- Ensure the user is authenticated
- Verify the user role is set to 'FARMER'

## Files Modified

1. `templates/users/profile.html` - Updated URL references
2. `templates/users/profile_display.html` - Added "Sell Product" buttons
3. `users/views.py` - Fixed duplicate profile function

## Quick Test Commands

```python
# In Django shell (python manage.py shell)
from users.models import User

# Check if you have farmer users
farmers = User.objects.filter(role='FARMER')
print(f"Farmers: {farmers.count()}")

# Get a farmer's details
farmer = farmers.first()
if farmer:
    print(f"Username: {farmer.username}")
    print(f"Role: {farmer.role}")
    print(f"Products: {farmer.products.count()}")
```

## Success Criteria

✅ Farmer can see "Sell Product" button on their profile
✅ Farmer can see "Add New Product" button above products
✅ Clicking buttons redirects to product creation page
✅ Buttons only appear for farmers on their own profile
✅ No errors when navigating or clicking buttons

## Notes

- The lint errors in the template files are false positives from the JavaScript linter trying to parse Django template syntax - they can be safely ignored
- All buttons use Bootstrap icons (bi-plus-circle, bi-plus-lg)
- Buttons maintain consistent styling with the rest of the application
