
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

print(f"GOOGLE_API_KEY set: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
print(f"GEMINI_API_KEY set: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

try:
    from agents.profile_agent import profile_builder
    print("Successfully imported profile_builder")
    
    # Try a simple run
    print("Attempting to run profile_builder...")
    response = profile_builder.run("This is a test CV content. Name: John Doe. Skills: Python.")
    print("Run successful!")
    print(response.content)
    
except Exception as e:
    print(f"Error running agent: {e}")
    import traceback
    traceback.print_exc()
