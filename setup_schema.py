import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.exception import AppwriteException

load_dotenv()

# Constants
DATABASE_ID = 'job-market-db'
COLLECTION_ID_JOBS = 'jobs'
COLLECTION_ID_APPLICATIONS = 'applications'
COLLECTION_ID_PROFILES = 'profiles'
COLLECTION_ID_ANALYTICS = 'analytics'
COLLECTION_ID_MATCHES = 'matches'

def setup_schema():
    print("Starting schema setup...")
    
    endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
    project_id = os.getenv('APPWRITE_PROJECT_ID')
    api_key = os.getenv('APPWRITE_API_KEY')

    missing = []
    if not endpoint: missing.append('APPWRITE_API_ENDPOINT')
    if not project_id: missing.append('APPWRITE_PROJECT_ID')
    if not api_key: missing.append('APPWRITE_API_KEY')

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        # Debug: check if .env exists
        if os.path.exists('.env'):
            print(".env file found.")
        else:
            print(".env file NOT found.")
        return

    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    databases = Databases(client)

    # 1. Ensure Database Exists
    try:
        databases.get(database_id=DATABASE_ID)
        print(f"Database '{DATABASE_ID}' exists.")
    except AppwriteException as e:
        if e.code == 404:
            print(f"Creating database '{DATABASE_ID}'...")
            databases.create(database_id=DATABASE_ID, name='Job Market DB')
        else:
            print(f"Error checking database: {e}")
            return

    # 2. Ensure Collections Exist
    collections = {
        COLLECTION_ID_PROFILES: 'Profiles',
        COLLECTION_ID_MATCHES: 'Job Matches',
        COLLECTION_ID_ANALYTICS: 'Analytics',
        COLLECTION_ID_APPLICATIONS: 'Applications',
        COLLECTION_ID_JOBS: 'Jobs' # Optional, but good to have
    }

    for col_id, col_name in collections.items():
        try:
            databases.get_collection(database_id=DATABASE_ID, collection_id=col_id)
            print(f"Collection '{col_name}' ({col_id}) exists.")
        except AppwriteException as e:
            if e.code == 404:
                print(f"Creating collection '{col_name}' ({col_id})...")
                databases.create_collection(
                    database_id=DATABASE_ID, 
                    collection_id=col_id, 
                    name=col_name,
                    document_security=False # Set to True if RLS needed, but for now False for simplicity
                )
            else:
                print(f"Error checking collection '{col_id}': {e}")

    # 3. Create Attributes for Profiles
    profile_attrs = [
        {'key': 'userId', 'type': 'string', 'size': 255, 'required': True},
        {'key': 'cv_file_id', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'cv_filename', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'cv_text', 'type': 'string', 'size': 10000000, 'required': False}, # Large size for text
        {'key': 'skills', 'type': 'string', 'size': 10000, 'required': False}, # JSON string
        {'key': 'experience_level', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'education', 'type': 'string', 'size': 1000, 'required': False},
        {'key': 'strengths', 'type': 'string', 'size': 10000, 'required': False}, # JSON string
        {'key': 'career_goals', 'type': 'string', 'size': 5000, 'required': False},
        {'key': 'notification_enabled', 'type': 'boolean', 'required': False, 'default': False},
        {'key': 'notification_threshold', 'type': 'integer', 'required': False, 'min': 0, 'max': 100, 'default': 70},
        {'key': 'updated_at', 'type': 'string', 'size': 64, 'required': False} # ISO timestamp
    ]
    
    ensure_attributes(databases, COLLECTION_ID_PROFILES, profile_attrs)

    # 4. Create Attributes for Matches
    matches_attrs = [
        {'key': 'userId', 'type': 'string', 'size': 255, 'required': True},
        {'key': 'location', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'matches', 'type': 'string', 'size': 10000000, 'required': False}, # JSON dump of matches
        {'key': 'last_seen', 'type': 'string', 'size': 64, 'required': False}
    ]
    ensure_attributes(databases, COLLECTION_ID_MATCHES, matches_attrs)

    # 5. Create Attributes for Analytics
    analytics_attrs = [
        {'key': 'userId', 'type': 'string', 'size': 255, 'required': True},
        {'key': 'event', 'type': 'string', 'size': 255, 'required': True},
        {'key': 'properties', 'type': 'string', 'size': 10000, 'required': False},
        {'key': 'page', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'created_at', 'type': 'string', 'size': 64, 'required': False}
    ]
    ensure_attributes(databases, COLLECTION_ID_ANALYTICS, analytics_attrs)

    # 6. Create Attributes for Applications
    app_attrs = [
        {'key': 'userId', 'type': 'string', 'size': 255, 'required': True},
        {'key': 'jobTitle', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'company', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'jobUrl', 'type': 'string', 'size': 1000, 'required': False},
        {'key': 'location', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'status', 'type': 'string', 'size': 50, 'required': False},
        {'key': 'files', 'type': 'string', 'size': 5000, 'required': False}, # JSON
    ]
    ensure_attributes(databases, COLLECTION_ID_APPLICATIONS, app_attrs)

def ensure_attributes(databases, collection_id, attributes):
    print(f"Ensuring attributes for {collection_id}...")
    for attr in attributes:
        key = attr['key']
        type_ = attr['type']
        
        try:
            if type_ == 'string':
                databases.create_string_attribute(DATABASE_ID, collection_id, key, size=attr.get('size', 255), required=attr.get('required', False), default=attr.get('default'))
            elif type_ == 'integer':
                databases.create_integer_attribute(DATABASE_ID, collection_id, key, min=attr.get('min', 0), max=attr.get('max', 1000000), required=attr.get('required', False), default=attr.get('default'))
            elif type_ == 'boolean':
                databases.create_boolean_attribute(DATABASE_ID, collection_id, key, required=attr.get('required', False), default=attr.get('default'))
            print(f"Created/Checked attribute '{key}' in '{collection_id}'")
        except Exception as e:
            if "already exists" in str(e):
                # print(f"Attribute '{key}' already exists in '{collection_id}'")
                pass
            else:
                print(f"Error creating attribute '{key}' in '{collection_id}': {e}")

if __name__ == "__main__":
    setup_schema()
