import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from ai_assistant.services import AIService

print("Testing Groq API Connection...")
try:
    response = AIService.chat_response("Hello, are you working?", language='en')
    print("\nSUCCESS! Response:")
    print(response)
except Exception as e:
    print("\nFAILED! Error:")
    print(e)
