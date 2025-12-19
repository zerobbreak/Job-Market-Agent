import os
from datetime import datetime
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID

class AppwriteService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppwriteService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.client = Client()
        
        endpoint = os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1')
        project_id = os.getenv('APPWRITE_PROJECT_ID')
        api_key = os.getenv('APPWRITE_API_KEY')

        if not project_id or not api_key:
            print("⚠️ Appwrite credentials not found. Persistent storage disabled.")
            self.enabled = False
            return

        self.client.set_endpoint(endpoint)
        self.client.set_project(project_id)
        self.client.set_key(api_key)
        
        self.db = Databases(self.client)
        self.storage = Storage(self.client)
        self.enabled = True
        
        # Configuration
        self.db_id = os.getenv('APPWRITE_DB_ID', 'job_market_db')
        self.bucket_id = os.getenv('APPWRITE_BUCKET_ID', 'application_files')

    def upload_file(self, file_path):
        """Upload a file to Appwrite Storage"""
        if not self.enabled:
            return None

        try:
            with open(file_path, 'rb') as f:
                result = self.storage.create_file(
                    bucket_id=self.bucket_id,
                    file_id=ID.unique(),
                    file=f
                )
            return result['$id']
        except Exception as e:
            print(f"❌ Error uploading file to Appwrite: {e}")
            return None

    def save_application(self, user_id, job_data, cv_file_id, cl_file_id):
        """Save application record to Database"""
        if not self.enabled:
            return None

        try:
            data = {
                'user_id': user_id,
                'job_title': job_data.get('title', 'Unknown'),
                'company': job_data.get('company', 'Unknown'),
                'job_url': job_data.get('url', ''),
                'status': 'applied',
                'cv_storage_id': cv_file_id,
                'cover_letter_storage_id': cl_file_id,
                'applied_date': datetime.now().isoformat()
            }
            
            result = self.db.create_document(
                database_id=self.db_id,
                collection_id='applications',
                document_id=ID.unique(),
                data=data
            )
            return result['$id']
        except Exception as e:
            print(f"❌ Error saving application to Appwrite: {e}")
            return None
