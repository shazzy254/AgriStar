from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('select-role/', views.select_role, name='select_role'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html', next_page='dashboard'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    # Address Routes (Must be before generic profile view)
    path('profile/add-address/', views.add_delivery_address, name='add_delivery_address'),
    path('profile/edit-address/<int:address_id>/', views.edit_delivery_address, name='edit_delivery_address'),
    path('profile/set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('profile/delete-address/<int:address_id>/', views.delete_address, name='delete_address'),

    # View OTHER user profile (Catch-all for profile/username)
    path('profile/<str:username>/', views.view_profile, name='view_profile'),
    
    # Specific Rider Routes
    path('rider/profile/edit/', views.rider_profile_edit, name='rider_profile_edit'),
    path('rider/profile/<str:username>/', views.view_rider_profile, name='view_rider_profile'),
    path('rider/accept-delivery/<int:order_id>/', views.accept_delivery, name='accept_delivery'),
    path('profile/update-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/toggle-availability/', views.toggle_rider_availability, name='toggle_rider_availability'),
    path('dashboard/withdraw/', views.rider_withdraw, name='rider_withdraw'),
    path('dashboard/update-location/', views.update_location, name='update_location'),
    
    # Rider functionality
    path('rider/order/<int:order_id>/accept/', views.accept_delivery, name='accept_delivery'),
    path('rider/order/<int:order_id>/reject/', views.reject_delivery, name='reject_delivery'),
    path('rider/order/<int:order_id>/update-status/', views.update_delivery_status, name='update_delivery_status'),
    path('rider/review/add/<int:rider_id>/', views.add_rider_review, name='add_rider_review'),
    
    # Rider Settings
    path('rider/settings/', views.rider_settings, name='rider_settings'),
    path('rider/settings/personal-info/', views.update_personal_info, name='update_personal_info'),
    path('rider/settings/vehicle-change/', views.request_vehicle_change, name='request_vehicle_change'),
    path('rider/settings/location/', views.update_location_settings, name='update_location_settings'),
    path('rider/upload-documents/', views.rider_upload_documents, name='rider_upload_documents'),
    
    # Reload
    path('api/locations/', views.get_locations, name='get_locations'),
    
    # Farmer Public Profile & Reviews
    path('farmer/<int:farmer_id>/', views.farmer_profile_public, name='farmer_profile_public'),
    path('farmer/<int:farmer_id>/review/', views.submit_review, name='submit_review'),
    path('farmer/<int:farmer_id>/toggle-favorite/', views.toggle_favorite_farmer, name='toggle_favorite_farmer'),
    path('favorites/farmers/', views.favorite_farmers_list, name='favorite_farmers_list'),
    
    # Admin Rider Verification
    path('admin/riders/verification/', views.admin_rider_verification_list, name='admin_rider_verification_list'),
    path('admin/riders/verification/<int:rider_id>/', views.admin_rider_verification_detail, name='admin_rider_verification_detail'),
    path('admin/riders/verification/<int:rider_id>/action/', views.admin_rider_verification_action, name='admin_rider_verification_action'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), 
         name='password_reset_confirm'),
]
