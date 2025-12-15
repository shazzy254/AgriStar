from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator

class Post(models.Model):
    """Community post model"""
    
    CATEGORY_CHOICES = [
        ('ADVICE', '💡 Advice'),
        ('MARKET', '📊 Market Update'),
        ('SALE', '🛒 For Sale'),
        ('ALERT', '🐛 Disease/Pest Alert'),
        ('WEATHER', '🌤️ Weather Update'),
        ('QA', '❓ Q&A'),
        ('GENERAL', '📝 General'),
    ]
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='posts'
    )
    content = models.TextField(help_text='Share your thoughts with the community')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='GENERAL'
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='liked_posts', 
        blank=True
    )
    is_pest_alert = models.BooleanField(default=False, help_text='Is this a pest/disease alert?')
    is_flagged = models.BooleanField(default=False, help_text='Is this post flagged for review?')
    tags = models.CharField(max_length=200, blank=True, default='')
    ai_diagnosis = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='community_videos/', blank=True, null=True)
    image = models.ImageField(upload_to='community_images/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.author.username} - {self.get_category_display()} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.count()


class PostImage(models.Model):
    """Multiple images for a post"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(
        upload_to='community_posts/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f'Image for post {self.post.id}'


class Comment(models.Model):
    """Comments on posts"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField()
    image = models.ImageField(upload_to='comment_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_comments',
        blank=True
    )
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.author.username} on {self.post.id}'
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    @property
    def likes_count(self):
        return self.likes.count()



class Follow(models.Model):
    """User follow system"""
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]
    
    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'


class SavedPost(models.Model):
    """Saved posts by users"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_posts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-saved_at']
    
    def __str__(self):
        return f'{self.user.username} saved post {self.post.id}'


class Report(models.Model):
    """Report system for inappropriate content"""
    
    REASON_CHOICES = [
        ('SPAM', '🚫 Spam'),
        ('HARASSMENT', '😡 Harassment'),
        ('INAPPROPRIATE', '⚠️ Inappropriate Content'),
        ('MISINFORMATION', '❌ Misinformation'),
        ('OTHER', '📝 Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Report by {self.reporter.username} on post {self.post.id}'
