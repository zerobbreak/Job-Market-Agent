import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    models = client.models.list()
    for m in models:
        print(f" - {m.name} (Supported: {m.supported_generation_methods})")
except Exception as e:
    print(f"Error listing models: {e}")
