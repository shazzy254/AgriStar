from django.db import models
from django.conf import settings

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_sessions')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'New Chat'}"

    class Meta:
        ordering = ['-updated_at']

class ChatMessage(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('bot', 'AI Assistant'),
    )
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField(blank=True)
    audio_file = models.FileField(upload_to='ai_audio/', blank=True, null=True)
    image_file = models.ImageField(upload_to='ai_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}..."
