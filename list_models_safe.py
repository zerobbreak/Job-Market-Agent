import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models (names only)...")
try:
    for m in client.models.list():
        try:
            print(f"Model: {m.name}")
        except:
            pass
except Exception as e:
    print(f"Error listing models: {e}")
