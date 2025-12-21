import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases

load_dotenv()

client = Client()
client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
client.set_key(os.getenv('APPWRITE_API_KEY'))

databases = Databases(client)

DATABASE_ID = 'job-market-db'
COLLECTION_ID_PROFILES = 'profiles'

try:
    print(f"Attempting to delete 'cv_text' attribute from {COLLECTION_ID_PROFILES}...")
    try:
        databases.delete_attribute(DATABASE_ID, COLLECTION_ID_PROFILES, 'cv_text')
        print("✓ Successfully deleted 'cv_text' attribute.")
    except Exception as e:
        print(f"✗ Failed to delete 'cv_text' (might not exist): {e}")

    try:
        databases.delete_attribute(DATABASE_ID, COLLECTION_ID_PROFILES, 'strengths')
        print("✓ Successfully deleted 'strengths' attribute.")
    except Exception as e:
        print(f"✗ Failed to delete 'strengths' (might not exist): {e}")

    # Also try to clean up other unused ones if needed, but cv_text is the big one.
    
    # Wait a bit or verify deletion?
    # Appwrite attribute deletion is async but usually fast enough for dev.

except Exception as e:
    print(f"Global Error: {e}")
