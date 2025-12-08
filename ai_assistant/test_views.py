import requests
from django.conf import settings
from django.http import JsonResponse
import os

def test_groq(request):
    """Test Groq API connection directly"""
    try:
        # Check if API key is loaded
        api_key = getattr(settings, 'GROQ_API_KEY', None)
        
        if not api_key:
            return JsonResponse({
                "error": "GROQ_API_KEY not found in settings",
                "env_check": os.getenv('GROQ_API_KEY', 'NOT FOUND'),
                "settings_check": "NOT FOUND"
            }, status=500)
        
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "llama-3.3-70b-versatile",  # Using the new active model
            "messages": [
                {"role": "user", "content": "Hello Groq, are you working?"}
            ],
            "max_tokens": 50
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return JsonResponse({
                "status": "SUCCESS",
                "groq_response": response.json(),
                "api_key_length": len(api_key),
                "model_used": "llama-3.3-70b-versatile"
            })
        else:
            return JsonResponse({
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text,
                "api_key_length": len(api_key),
                "model_used": "llama-3.3-70b-versatile"
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "type": type(e).__name__
        }, status=500)
