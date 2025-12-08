from django.http import JsonResponse
from django.conf import settings
import os

def debug_ai_config(request):
    """Debug view to check AI configuration"""
    return JsonResponse({
        'GROQ_API_KEY_set': bool(getattr(settings, 'GROQ_API_KEY', None)),
        'GROQ_API_KEY_length': len(getattr(settings, 'GROQ_API_KEY', '')) if getattr(settings, 'GROQ_API_KEY', None) else 0,
        'GROQ_MODEL': getattr(settings, 'GROQ_MODEL', 'NOT SET'),
        'env_GROQ_API_KEY_set': bool(os.getenv('GROQ_API_KEY')),
        'env_GROQ_MODEL': os.getenv('GROQ_MODEL', 'NOT SET'),
    })
