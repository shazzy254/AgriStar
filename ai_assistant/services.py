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
        Chat assistant response using Groq API.
        """
        from django.conf import settings
        from openai import OpenAI

        try:
            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )

            system_content = "You are AgriStar, an expert agricultural assistant in Kenya. Help farmers with crops, pests, market prices, and farming advice. Structure your responses clearly. For steps or lists, use bullet points (each on a new line). Keep your tone warm and friendly. "
            if language == 'sw':
                system_content += "Respond in Kiswahili."
            else:
                system_content += "Respond in English."

            completion = client.chat.completions.create(
                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service right now. Please try again later."

    @staticmethod
    def transcribe_audio(audio_file):
        """
        Transcribe audio using Groq Whisper model.
        """
        from django.conf import settings
        from openai import OpenAI

        try:
            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            
            transcription = client.audio.transcriptions.create(
                file=(audio_file.name, audio_file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
            return transcription
        except Exception as e:
            print(f"Groq Audio Error: {e}")
            return None

    @staticmethod
    def analyze_image(image_file, prompt="Describe this image in detail.", language='en'):
        """
        Analyze image using Groq Vision model.
        """
        from django.conf import settings
        from openai import OpenAI
        import base64

        try:
            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            
            # Encode image to base64
            image_content = image_file.read()
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            system_instruction = "You are an agricultural expert. Analyze the provided image focusing on crops, pests, diseases, or soil conditions. Structure your findings in a clear list using bullet points. Keep your tone warm and friendly."
            if language == 'sw':
                system_instruction += " Respond in Kiswahili."

            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    },
                    {
                        "role": "system",
                        "content": system_instruction
                    }
                ],
                temperature=0.5,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Groq Vision Error: {e}")
            return "Sorry, I couldn't analyze the image. Please try again."

    @staticmethod
    def translate_text(text, target_lang='sw'):
        """
        Mock translation.
        """
        if target_lang == 'sw':
            return f"[SW] {text}"
        return f"[EN] {text}"
