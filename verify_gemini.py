import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"API Key present: {bool(api_key)}")

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-2.0-flash",
    "gemini-pro"
]

print("Testing models...")
for model_id in models_to_test:
    print(f"\nTesting: {model_id}")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Say hello"
        )
        print(f"SUCCESS! {model_id} worked.")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"FAILED: {model_id}")
        print(f"Error: {e}")
