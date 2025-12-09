from django.urls import path
from . import views

urlpatterns = [
    path('', views.AssistantView.as_view(), name='ai_assistant_index'),
    path('history/<int:session_id>/', views.ChatHistoryView.as_view(), name='chat_history'),
    path('chat/', views.ChatView.as_view(), name='ai_chat'),
    path('voice/', views.VoiceChatView.as_view(), name='ai_voice_chat'),
    path('vision/', views.VisionChatView.as_view(), name='ai_vision_chat'),
    path('public-chat/', views.PublicChatView.as_view(), name='public_chat'),
    path('diagnose/', views.DiagnoseView.as_view(), name='diagnose'),
    path('translate/', views.TranslateView.as_view(), name='translate'),
]
