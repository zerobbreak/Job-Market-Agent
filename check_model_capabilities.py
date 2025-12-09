import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables.")
    print("Please set it in your .env file or environment.")
    import sys
    sys.exit(1)

client = genai.Client(api_key=api_key)

models_to_check = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash-exp",
    "gemini-pro"
]

print("Checking model capabilities...")
for m in client.models.list():
    # Check if model name (minus 'models/') is in our list
    short_name = m.name.replace('models/', '')
    if short_name in models_to_check or m.name in models_to_check:
        print(f"\nModel: {m.name}")
        print(f"Supported Methods: {m.supported_generation_methods}")
