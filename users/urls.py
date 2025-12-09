from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('select-role/', views.select_role, name='select_role'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('profile/add-address/', views.add_delivery_address, name='add_delivery_address'),
    path('profile/set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('profile/delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Farmer Public Profile & Reviews
    path('farmer/<int:farmer_id>/', views.farmer_profile_public, name='farmer_profile_public'),
    path('farmer/<int:farmer_id>/review/', views.submit_review, name='submit_review'),
    path('farmer/<int:farmer_id>/toggle-favorite/', views.toggle_favorite_farmer, name='toggle_favorite_farmer'),
    path('favorites/farmers/', views.favorite_farmers_list, name='favorite_farmers_list'),
    
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

