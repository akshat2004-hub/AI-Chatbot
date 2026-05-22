import requests
import json

url = "http://127.0.0.1:8001/chat"
headers = {"Content-Type": "application/json"}

def test_chat(msg):
    data = {"question": msg, "session_id": "test_123"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"User: {msg}")
    print(f"Bot: {response.json().get('message', 'N/A')}")
    print("-" * 30)

try:
    test_chat("Hi, I want a mobile app.")
    test_chat("My name is Akshat and email is akshat@gmail.com")
    test_chat("My budget is $5k-$10k and I want a senior dev.")
except Exception as e:
    print(f"Error: {e}")
