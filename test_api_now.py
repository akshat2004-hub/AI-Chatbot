"""Test exact models used in config with LangChain"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
from langchain_google_genai import ChatGoogleGenerativeAI

models = [
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash",
]

print("Testing LangChain models...\n")
for model in models:
    try:
        llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0.3)
        resp = llm.invoke("Say OK only.")
        content = resp.content
        if isinstance(content, list):
            content = " ".join([c.get("text","") if isinstance(c,dict) else str(c) for c in content])
        print(f"WORKS: {model} -> {str(content)[:40]}")
    except Exception as e:
        print(f"FAIL: {model} -> {str(e)[:120]}")
