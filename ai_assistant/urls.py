from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='ai_chat'),
    path('diagnose/', views.DiagnoseView.as_view(), name='ai_diagnose'),
    path('translate/', views.TranslateView.as_view(), name='ai_translate'),
]
