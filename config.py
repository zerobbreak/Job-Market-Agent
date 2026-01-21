import os
from dotenv import load_dotenv
from appwrite.client import Client

load_dotenv()

class Config:
    # API Settings
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(24).hex()
    
    # Appwrite Settings
    APPWRITE_ENDPOINT = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
    APPWRITE_PROJECT_ID = os.getenv('APPWRITE_PROJECT_ID')
    APPWRITE_API_KEY = os.getenv('APPWRITE_API_KEY')
    
    # Database and Storage IDs
    DATABASE_ID = 'job-market-db'
    COLLECTION_ID_JOBS = 'jobs'
    COLLECTION_ID_APPLICATIONS = 'applications'
    COLLECTION_ID_PROFILES = 'profiles'
    BUCKET_ID_CVS = 'cv-bucket'
    COLLECTION_ID_ANALYTICS = 'analytics'
    COLLECTION_ID_MATCHES = 'matches'
    
    # File Sub-settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Security
    SIGNED_URL_SECRET = os.getenv('SIGNED_URL_SECRET') or SECRET_KEY
    SIGNED_URL_EXPIRY_SECONDS = 3600
    OTP_EXPIRY_SECONDS = 300
    
    @staticmethod
    def init_appwrite_client():
        client = Client()
        client.set_endpoint(Config.APPWRITE_ENDPOINT)
        client.set_project(Config.APPWRITE_PROJECT_ID)
        return client
