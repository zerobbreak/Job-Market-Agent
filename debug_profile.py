
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print(f"GOOGLE_API_KEY present: {'GOOGLE_API_KEY' in os.environ}")
if 'GOOGLE_API_KEY' in os.environ:
    print(f"Key length: {len(os.environ['GOOGLE_API_KEY'])}")

from main import JobApplicationPipeline

# Mock CV content
cv_content = """
John Doe
Software Developer
Skills: Python, React, SQL
Experience: 3 years at Tech Co
Education: BS Computer Science
"""

try:
    print("Initializing pipeline...")
    pipeline = JobApplicationPipeline()
    
    print("Building profile...")
    profile = pipeline.build_profile(cv_content)
    
    if profile:
        print("Success! Profile built:")
        print(profile)
    else:
        print("Failed to build profile (returned None)")

except Exception as e:
    print(f"Caught exception: {e}")
    import traceback
    traceback.print_exc()
