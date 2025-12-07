import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing first 10 models...")
try:
    count = 0
    for m in client.models.list():
        print(f"Model: {m.name}")
        count += 1
        if count >= 10:
            break
except Exception as e:
    print(f"Error listing models: {e}")
