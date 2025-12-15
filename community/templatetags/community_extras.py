from django import template
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
import re
from django.urls import reverse

register = template.Library()

@register.filter(name='process_mentions')
def process_mentions(value):
    """
    Replaces @username with a link to the user's profile.
    Example: "Hello @monicah" -> "Hello <a href='/user/1/'>@monicah</a>"
    """
    if not value:
        return ""
    
    # Pattern to match @username (assuming usernames are alphanumeric based on typical Django user model)
    # matching @ followed by word characters
    pattern = r'@(\w+)'
    
    def replace_match(match):
        username = match.group(1)
        User = get_user_model()
        try:
            # Try to find the user. Case insensitive match might be safer.
            user = User.objects.get(username__iexact=username)
            # Link to the user profile
            url = reverse('user_profile', args=[user.id])
            return f'<a href="{url}" class="text-primary fw-bold text-decoration-none">@{username}</a>'
        except User.DoesNotExist:
            # If user not found, leave text as is or just highlight
            return f'<span class="text-muted">@{username}</span>'

    # Substitute using the replacement function
    return mark_safe(re.sub(pattern, replace_match, value))

from community.models import Follow

@register.filter(name='is_following')
def is_following(author_id, user):
    """
    Checks if the user follows the author (by ID).
    Usage: {{ author.id|is_following:user }}
    """
    if not user.is_authenticated:
        return False
    return Follow.objects.filter(follower=user, following_id=author_id).exists()
