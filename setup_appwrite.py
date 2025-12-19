
import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException

load_dotenv('.env')

client = Client()
endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
project = os.getenv('APPWRITE_PROJECT_ID')
key = os.getenv('APPWRITE_API_KEY')

if not project or not key:
    print("Error: APPWRITE_PROJECT_ID and APPWRITE_API_KEY refer required.")
    exit(1)

client.set_endpoint(endpoint)
client.set_project(project)
client.set_key(key)

databases = Databases(client)

DATABASE_ID = 'job-market-db'

# Define Collections and their Attributes
collections = {
    'matches': {
        'name': 'Matches',
        'attributes': [
            {'type': 'string', 'key': 'userId', 'size': 255, 'required': True},
            {'type': 'string', 'key': 'location', 'size': 255, 'required': False},
            {'type': 'string', 'key': 'matches', 'size': 1000000, 'required': False}, # Long text
            {'type': 'string', 'key': 'last_seen', 'size': 255, 'required': False},
        ],
        'indexes': [
            {'key': 'idx_user_loc', 'type': 'key', 'attributes': ['userId', 'location']},
            {'key': 'idx_user_created', 'type': 'key', 'attributes': ['userId']}, # for order_desc($createdAt)
        ]
    },
    'profiles': {
        'name': 'Profiles',
        'attributes': [
            {'type': 'string', 'key': 'userId', 'size': 255, 'required': True},
            {'type': 'string', 'key': 'skills', 'size': 1000000, 'required': False},
            {'type': 'string', 'key': 'experience_level', 'size': 255, 'required': False},
            {'type': 'string', 'key': 'education', 'size': 1024, 'required': False},
            {'type': 'string', 'key': 'strengths', 'size': 1000000, 'required': False},
            {'type': 'string', 'key': 'career_goals', 'size': 5000, 'required': False},
            {'type': 'string', 'key': 'cv_filename', 'size': 255, 'required': False},
            {'type': 'string', 'key': 'cv_text', 'size': 1000000, 'required': False},
            {'type': 'string', 'key': 'cv_file_id', 'size': 255, 'required': False},
            {'type': 'boolean', 'key': 'notification_enabled', 'required': False, 'default': False},
            {'type': 'integer', 'key': 'notification_threshold', 'required': False, 'default': 70},
            {'type': 'string', 'key': 'updated_at', 'size': 255, 'required': False},
        ],
        'indexes': [
             {'key': 'idx_user', 'type': 'unique', 'attributes': ['userId']},
        ]
    },
    'analytics': {
        'name': 'Analytics',
        'attributes': [
            {'type': 'string', 'key': 'userId', 'size': 255, 'required': True},
            {'type': 'string', 'key': 'event', 'size': 255, 'required': True},
            {'type': 'string', 'key': 'properties', 'size': 1000000, 'required': False},
            {'type': 'string', 'key': 'page', 'size': 255, 'required': False},
            {'type': 'string', 'key': 'created_at', 'size': 255, 'required': False},
        ]
    },
    'applications': {
        'name': 'Applications',
        'attributes': [
            {'type': 'string', 'key': 'userId', 'size': 255, 'required': True},
            {'type': 'string', 'key': 'status', 'size': 50, 'required': False},
             # Add other potentially needed fields
        ]
    },
    'jobs': {
        'name': 'Jobs',
        'attributes': [] # Define if needed
    }
}

def setup():
    # 1. Create Database
    try:
        databases.get(DATABASE_ID)
        print(f"Database '{DATABASE_ID}' exists.")
    except AppwriteException as e:
        if e.code == 404:
            print(f"Creating database '{DATABASE_ID}'...")
            databases.create(DATABASE_ID, 'Job Market Database')
        else:
            print(f"Error getting database: {e}")
            return

    # 2. Create Collections
    for coll_id, config in collections.items():
        try:
            databases.get_collection(DATABASE_ID, coll_id)
            print(f"Collection '{coll_id}' exists.")
        except AppwriteException as e:
            if e.code == 404:
                print(f"Creating collection '{coll_id}'...")
                databases.create_collection(DATABASE_ID, coll_id, config['name'])
            else:
                print(f"Error checking collection '{coll_id}': {e}")
                continue
        
        # 3. Create Attributes
        for attr in config['attributes']:
            try:
                # Determine method based on type
                if attr['type'] == 'string':
                    databases.create_string_attribute(DATABASE_ID, coll_id, attr['key'], attr['size'], attr['required'], default=attr.get('default'))
                elif attr['type'] == 'integer':
                    databases.create_integer_attribute(DATABASE_ID, coll_id, attr['key'], attr['required'], min=None, max=None, default=attr.get('default'))
                elif attr['type'] == 'boolean':
                    databases.create_boolean_attribute(DATABASE_ID, coll_id, attr['key'], attr['required'], default=attr.get('default'))
                print(f"  + Attribute '{attr['key']}' ensured.")
            except AppwriteException as e:
                if e.code == 409: # Conflict (already exists)
                    pass
                else:
                    print(f"  ! Error creating attribute '{attr['key']}': {e}")
        
        # 4. Create Indexes
        if 'indexes' in config:
            for idx in config['indexes']:
                try:
                    databases.create_index(DATABASE_ID, coll_id, idx['key'], idx['type'], idx['attributes'])
                    print(f"  + Index '{idx['key']}' created.")
                except AppwriteException as e:
                    if e.code == 409:
                        pass
                    else:
                        print(f"  ! Error creating index '{idx['key']}': {e}")

if __name__ == "__main__":
    setup()
