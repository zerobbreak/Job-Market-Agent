import logging
from appwrite.services.databases import Databases
from config import Config

logger = logging.getLogger(__name__)

class AppwriteModel:
    @staticmethod
    def ensure_schema(client):
        try:
            db = Databases(client)
            # Basic check for profile attributes
            # In a full modular setup, we'd have detailed migration logic here
            logger.info("Verifying database schema...")
            # Placeholder for schema verification logic from main.py
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")

    @staticmethod
    def get_user_profile(db, user_id):
        from appwrite.query import Query
        return db.list_documents(
            database_id=Config.DATABASE_ID,
            collection_id=Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', user_id)]
        )
