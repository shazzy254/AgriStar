# ai_assistant/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """
    Represents a conversation thread between a user and the AI assistant.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Conversation'} ({self.created_at.strftime('%Y-%m-%d')})"

    def save(self, *args, **kwargs):
        # Auto-generate title from first message if not set
        if not self.title and not self.pk:
            self.title = f"Chat {timezone.now().strftime('%b %d, %Y %I:%M %p')}"
        super().save(*args, **kwargs)

    def get_message_count(self):
        return self.messages.count()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """
    Represents a single message in a conversation.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    image = models.ImageField(
        upload_to='ai_assistant/images/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Crop image for pest/disease detection'
    )
    image_analysis = models.JSONField(
        blank=True,
        null=True,
        help_text='AI analysis results for uploaded image'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    def has_image(self):
        return bool(self.image)

    def get_analysis_summary(self):
        """Extract key info from image analysis JSON."""
        if not self.image_analysis:
            return None
        return {
            'detected': self.image_analysis.get('detected_issue'),
            'severity': self.image_analysis.get('severity'),
            'confidence': self.image_analysis.get('confidence')
        }
