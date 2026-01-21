import os
import logging
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def fix_schema():
    client = Client()
    endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
    project_id = os.getenv('APPWRITE_PROJECT_ID')
    api_key = os.getenv('APPWRITE_API_KEY')
    
    if not all([endpoint, project_id, api_key]):
        logger.error("Missing Appwrite credentials")
        return

    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)

    db = Databases(client)
    
    database_id = 'job-market-db'
    collection_id = 'jobs'
    
    logger.info(f"Checking schema for collection {collection_id} in database {database_id}...")
    
    # Define expected attributes
    # key, type, size/required/default
    # types: string, integer, boolean
    attributes = [
        {'key': 'status', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'progress', 'type': 'integer', 'required': False},
        {'key': 'phase', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'job_data', 'type': 'string', 'size': 1000000, 'required': False}, # 1MB
        {'key': 'result', 'type': 'string', 'size': 1000000, 'required': False},    # 1MB
        {'key': 'template_type', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'user_id', 'type': 'string', 'size': 255, 'required': False},
        {'key': 'error', 'type': 'string', 'size': 10000, 'required': False}
    ]
    
    try:
        # Get existing attributes
        existing_attrs = db.list_attributes(database_id, collection_id)
        existing_keys = [attr['key'] for attr in existing_attrs['attributes']]
        
        for attr in attributes:
            if attr['key'] not in existing_keys:
                logger.info(f"Creating attribute: {attr['key']}")
                try:
                    if attr['type'] == 'string':
                        db.create_string_attribute(
                            database_id, collection_id, 
                            attr['key'], attr['size'], 
                            required=attr['required']
                        )
                    elif attr['type'] == 'integer':
                        db.create_integer_attribute(
                            database_id, collection_id, 
                            attr['key'], 
                            required=attr['required']
                        )
                    logger.info(f"Created attribute {attr['key']}")
                except Exception as e:
                    logger.error(f"Failed to create attribute {attr['key']}: {e}")
            else:
                logger.info(f"Attribute {attr['key']} already exists")
                
        # Check for Indexes
        # status needs an index for querying
        existing_indexes = db.list_indexes(database_id, collection_id)
        existing_index_keys = [idx['key'] for idx in existing_indexes['indexes']]
        
        index_key = 'status'
        if index_key not in existing_index_keys and not any(index_key in idx['attributes'] for idx in existing_indexes['indexes']):
             logger.info(f"Creating index for {index_key}...")
             try:
                 db.create_index(
                     database_id, collection_id,
                     'status_index',
                     'key',
                     [index_key]
                 )
                 logger.info(f"Created index status_index")
             except Exception as e:
                 logger.error(f"Failed to create index for {index_key}: {e}")
        else:
             logger.info(f"Index for {index_key} already exists")

    except Exception as e:
        logger.error(f"Error checking/fixing schema: {e}")

if __name__ == '__main__':
    fix_schema()
