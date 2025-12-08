import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
print(f"API Key loaded: {api_key[:20]}..." if api_key else "NO API KEY!")

url = "https://api.groq.com/openai/v1/chat/completions"

payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello"}
    ],
    "max_tokens": 50
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print("Testing Groq API...")
response = requests.post(url, json=payload, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"AI Response: {data['choices'][0]['message']['content']}")
else:
    print(f"ERROR: {response.text}")
