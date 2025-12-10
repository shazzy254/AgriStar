
from django.urls import path
from .views import mpesa_callback, b2c_result, b2c_timeout

urlpatterns = [
    path('callback/', mpesa_callback, name='mpesa_callback'),
    path('b2c_result/', b2c_result, name='b2c_result'),
    path('b2c_timeout/', b2c_timeout, name='b2c_timeout'),
]