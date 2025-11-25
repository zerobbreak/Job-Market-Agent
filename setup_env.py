
import os
import sys

def setup_environment():
    print("\n" + "="*50)
    print("🔧 Job Market Agent - Environment Setup")
    print("="*50)
    
    env_path = ".env"
    
    # Check if .env already exists
    if os.path.exists(env_path):
        print(f"\nFound existing {env_path} file.")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return

    print("\nTo use the AI features, you need a Google API Key (Gemini).")
    print("You can get one here: https://aistudio.google.com/app/apikey")
    
    api_key = input("\nEnter your Google API Key: ").strip()
    
    if not api_key:
        print("Error: API Key cannot be empty.")
        return

    print("\n--- Appwrite Configuration (Optional) ---")
    print("To enable User Accounts and History, you need an Appwrite Project.")
    print("Create one at: https://cloud.appwrite.io/")
    
    use_appwrite = input("Do you want to configure Appwrite now? (y/n): ").lower().strip()
    
    appwrite_endpoint = "https://cloud.appwrite.io/v1"
    appwrite_project_id = ""
    appwrite_api_key = ""
    
    if use_appwrite == 'y':
        appwrite_project_id = input("Enter Appwrite Project ID: ").strip()
        appwrite_api_key = input("Enter Appwrite API Key: ").strip()
        endpoint_input = input("Enter Appwrite Endpoint (default: https://cloud.appwrite.io/v1): ").strip()
        if endpoint_input:
            appwrite_endpoint = endpoint_input
        
    # Create .env content
    env_content = f"""# Job Market Agent Configuration
GOOGLE_API_KEY={api_key}

# Appwrite Configuration (Optional - for Persistent Storage & Auth)
APPWRITE_ENDPOINT={appwrite_endpoint}
APPWRITE_PROJECT_ID={appwrite_project_id}
APPWRITE_API_KEY={appwrite_api_key}
APPWRITE_DB_ID=job_market_db
APPWRITE_BUCKET_ID=application_files

# Optional: Default Search Settings
SEARCH_QUERY=Python Developer
LOCATION=South Africa
MAX_JOBS=10
"""
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print(f"\n✅ Successfully created {env_path}!")
        print("You can now restart the application to use AI features.")
        
    except Exception as e:
        print(f"\n❌ Error creating file: {e}")

if __name__ == "__main__":
    setup_environment()
