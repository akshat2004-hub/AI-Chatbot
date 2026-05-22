import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)

print("Status:", response.status_code)
if response.status_code == 200:
    chat_models = [m['name'] for m in response.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
    print("Available chat models:")
    for m in chat_models:
        print(" -", m)
else:
    print(response.text)
