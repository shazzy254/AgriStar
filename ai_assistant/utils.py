# ai_assistant/utils.py
"""
AgriStar AI Assistant Utilities
Handles all AI interactions: text chat, image analysis, and image generation
"""

import os
import requests
import logging
import base64
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_BASE = "https://api.groq.com/openai/v1"


def get_agristar_system_prompt():
    """
    System prompt that makes AI specialized for AgriStar farming platform.
    """
    return """You are AgriStar AI Assistant - a specialized farming expert for Kenyan farmers.

CORE IDENTITY:
- You ONLY help with farming, agriculture, and AgriStar platform features
- You are friendly, practical, and speak like a helpful farming extension officer
- You provide actionable, step-by-step advice

LANGUAGE RULES:
- If user writes in Kiswahili, respond ONLY in Kiswahili
- If user writes in English, respond ONLY in English
- Never mix languages in one response

EXPERTISE AREAS:
1. Crop Management: planting, watering, fertilizing, harvesting
2. Pest & Disease Control: identification, treatment, prevention
3. Soil Health: testing, improvement, crop rotation
4. Weather & Climate: seasonal planning, drought/flood management
5. Market Prices: when to sell, where to sell, pricing strategies
6. AgriStar Platform: how to use marketplace, orders, AI features

RESPONSE STYLE:
- Keep answers 3-6 steps maximum
- Use simple language (Grade 8 level)
- Include specific measurements (e.g., "2 liters per plant")
- Mention local Kenyan context when relevant
- If you don't know, say so and suggest consulting an extension officer

WHAT YOU DON'T DO:
- Medical advice for humans
- Legal advice
- Financial investment advice
- Topics unrelated to farming

Remember: You're helping real farmers grow better crops and earn more income!"""


def call_groq_chat(messages, model=None, max_tokens=800, temperature=0.7):
    """
    Call Groq API for text chat.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (defaults to settings.GROQ_MODEL)
        max_tokens: Maximum response length
        temperature: Creativity level (0-1)
    
    Returns:
        str: AI response text
    """
    model = model or getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
    api_key = getattr(settings, 'GROQ_API_KEY', None)
    
    if not api_key:
        logger.error("GROQ_API_KEY not configured in settings")
        return "Samahani, AI haipo sasa. / Sorry, AI is unavailable right now."
    
    url = f"{GROQ_API_BASE}/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        logger.info(f"Calling Groq chat API with model: {model}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            logger.info("Groq chat API call successful")
            return content
        else:
            logger.error(f"Unexpected Groq response format: {data}")
            return "Samahani, kuna tatizo. / Sorry, there was an error."
            
    except requests.exceptions.Timeout:
        logger.error("Groq API timeout")
        return "Samahani, AI inachukua muda mrefu. Jaribu tena. / Sorry, AI is taking too long. Try again."
    except requests.exceptions.HTTPError as e:
        logger.error(f"Groq API HTTP error: {e.response.status_code}")
        logger.error(f"Groq API error response: {e.response.text}")
        return "Samahani, kuna tatizo na AI. / Sorry, AI service error."
    except Exception as e:
        logger.exception("Groq API call failed")
        return "Samahani, kuna tatizo. Jaribu tena. / Sorry, an error occurred. Try again."


def analyze_crop_image(image_file):
    """
    Analyze crop image for pests, diseases, or health issues using AI vision.
    
    Args:
        image_file: Django UploadedFile object
    
    Returns:
        dict: Analysis results with detected_issue, severity, confidence, treatment, prevention
    """
    api_key = getattr(settings, 'GROQ_API_KEY', None)
    if not api_key:
        return {"error": "API key not configured"}
    
    try:
        # Read and encode image
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        image_file.seek(0)  # Reset file pointer
        
        # Vision analysis prompt
        vision_prompt = """Analyze this crop/plant image for agricultural issues.

Provide a structured response:
- Detected Issue: [specific pest/disease name or "Healthy crop" or "Cannot determine"]
- Severity: [Low/Medium/High/Critical]
- Confidence: [0-100]%
- Treatment: [3-5 specific actionable steps for Kenyan farmers]
- Prevention: [3-5 prevention tips]

Be specific and practical. If you're not sure, say so."""

        url = f"{GROQ_API_BASE}/chat/completions"
        
        payload = {
            "model": "llama-3.2-90b-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        logger.info("Calling Groq vision API for image analysis")
        response = requests.post(url, json=payload, headers=headers, timeout=45)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            analysis_text = data["choices"][0]["message"]["content"]
            logger.info("Image analysis successful")
            return parse_analysis_text(analysis_text)
        else:
            logger.error(f"Unexpected vision API response: {data}")
            return {"error": "Failed to analyze image"}
            
    except Exception as e:
        logger.exception("Image analysis failed")
        return {
            "error": str(e),
            "detected_issue": "Analysis failed",
            "severity": "Unknown",
            "confidence": 0,
            "treatment": ["Please try uploading a clearer image"],
            "prevention": []
        }


def parse_analysis_text(text):
    """Parse AI vision response into structured format."""
    result = {
        "detected_issue": "Unknown",
        "severity": "Unknown",
        "confidence": 50,
        "treatment": [],
        "prevention": []
    }
    
    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse key-value pairs
        if "detected issue:" in line.lower():
            result["detected_issue"] = line.split(':', 1)[1].strip()
        elif "severity:" in line.lower():
            result["severity"] = line.split(':', 1)[1].strip()
        elif "confidence:" in line.lower():
            conf_str = line.split(':', 1)[1].strip().replace('%', '').strip()
            try:
                result["confidence"] = int(conf_str)
            except:
                result["confidence"] = 50
        elif "treatment:" in line.lower():
            current_section = "treatment"
        elif "prevention:" in line.lower():
            current_section = "prevention"
        elif line.startswith(('-', '•', '*')) or (line[0].isdigit() and '.' in line[:3]):
            # This is a list item
            item = line.lstrip('-•*0123456789. ').strip()
            if current_section == "treatment" and item:
                result["treatment"].append(item)
            elif current_section == "prevention" and item:
                result["prevention"].append(item)
    
    return result
