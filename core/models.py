from django.db import models
from django.conf import settings

class FarmerSchedule(models.Model):
    EVENT_TYPES = [
        ('PLANTING', 'Planting'),
        ('HARVESTING', 'Harvesting'),
        ('FERTILIZING', 'Fertilizing'),
        ('IRRIGATION', 'Irrigation'),
        ('MEETING', 'Meeting'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules')
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='OTHER')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)
    is_reminder = models.BooleanField(default=True)
    reminder_minutes = models.PositiveIntegerField(default=30, help_text="Minutes before event to notify")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return f"{self.title} ({self.start_time})"

class JournalEntry(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = "Journal Entries"
    
    def __str__(self):
        return f"{self.title} - {self.date}"
