import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

candidates = [
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro-002",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-2.0-flash-exp", # We know this 429s
]

print(f"Testing {len(candidates)} models for availability...")

for model_id in candidates:
    print(f"\n--- Testing {model_id} ---")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Hello, are you working?"
        )
        print(f"✅ SUCCESS: {model_id}")
        print(f"Response: {response.text[:50]}...")
        # If we find one that works and IS NOT the 429 prone one, we might want to stop.
        # But let's check them all to see options.
    except errors.ClientError as e:
        print(f"❌ FAILED: {model_id}")
        print(f"Status: {e.code} - {e.message}")
    except Exception as e:
        print(f"❌ ERROR: {model_id}")
        print(f"Details: {str(e)}")
    
    time.sleep(1) # Be nice to the API
