import os
import logging
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def fix_error_attr():
    client = Client()
    endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
    project_id = os.getenv('APPWRITE_PROJECT_ID')
    api_key = os.getenv('APPWRITE_API_KEY')
    
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    db = Databases(client)
    
    database_id = 'job-market-db'
    collection_id = 'jobs'
    
    try:
        logger.info("Attempting to create 'error' attribute with smaller size...")
        db.create_string_attribute(
            database_id, collection_id, 
            'error', 5000, 
            required=False
        )
        logger.info("Created attribute 'error' successfully")
    except Exception as e:
        logger.error(f"Failed to create attribute 'error': {e}")
        
        # If it fails, maybe we need to delete it first if it exists in a broken state?
        # But usually it just doesn't exist.

if __name__ == '__main__':
    fix_error_attr()
