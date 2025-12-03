from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import confirm_delivery

router = DefaultRouter()
router.register(r'api/products', views.ProductViewSet)
router.register(r'api/orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('create/', views.create_product, name='create_product'),
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    
    # Payment URLs
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('payment/<int:order_id>/initiate/', views.initiate_payment, name='initiate_payment'),
    
    # Favorites URLs
    path('favorites/', views.view_saved_products, name='view_saved_products'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # Notifications URLs
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('confirm-delivery/<int:order_id>/', views.confirm_delivery, name='confirm_delivery'),
    path('order/<int:order_id>/accept/', views.accept_order, name='accept_order'),
    path('order/<int:order_id>/reject/', views.reject_order, name='reject_order'),
    path('', include(router.urls)),
]
