from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.user_list, name='admin_user_list'),
    path('users/<int:user_id>/verify/', views.verify_user, name='admin_verify_user'),
    path('users/<int:user_id>/suspend/', views.suspend_user, name='admin_suspend_user'),
    
    # Product Management
    path('products/approval/', views.product_approval, name='admin_product_approval'),
    path('products/<int:product_id>/approve/', views.approve_product, name='admin_approve_product'),
    path('products/<int:product_id>/reject/', views.reject_product, name='admin_reject_product'),
    

]
