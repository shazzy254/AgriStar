import os
import random
import time

# Mock Services for Development
# In production, replace these with actual API calls to OpenAI, HuggingFace, etc.

class AIService:
    @staticmethod
    def diagnose_pest(image_file):
        """
        Mock pest diagnosis.
        Returns label, confidence, and remediation.
        """
        # Simulate processing time
        time.sleep(1)
        
        # Mock response
        diagnoses = [
            {
                "label": "Fall Armyworm",
                "confidence": 0.95,
                "remediation": "Use pheromone traps and biological control agents like Trichogramma."
            },
            {
                "label": "Tomato Blight",
                "confidence": 0.88,
                "remediation": "Remove infected leaves immediately and apply copper-based fungicides."
            },
            {
                "label": "Healthy",
                "confidence": 0.99,
                "remediation": "No action needed. Keep monitoring."
            }
        ]
        return random.choice(diagnoses)

    @staticmethod
    def chat_response(message, language='en'):
        """
        Mock chat assistant response.
        """
        time.sleep(1)
        if language == 'sw':
            return f"Hii ni jibu la majaribio kwa: {message}"
        return f"This is a mock AI response to: {message}"

    @staticmethod
    def translate_text(text, target_lang='sw'):
        """
        Mock translation.
        """
        if target_lang == 'sw':
            return f"[SW] {text}"
        return f"[EN] {text}"
