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
    with open('schema_dump.txt', 'w') as f:
        f.write(f"Fetching attributes for collection: {COLLECTION_ID_PROFILES}...\n")
        attrs = databases.list_attributes(DATABASE_ID, COLLECTION_ID_PROFILES)
        f.write(f"Total Attributes: {attrs['total']}\n")
        f.write("-" * 40 + "\n")
        for attr in attrs['attributes']:
            key = attr.get('key')
            atype = attr.get('type')
            status = attr.get('status')
            size = attr.get('size', 'N/A')
            f.write(f"- {key} ({atype}) [size: {size}] [{status}]\n")
    print("Dumped to schema_dump.txt")
        
except Exception as e:
    print(f"Error: {e}")
