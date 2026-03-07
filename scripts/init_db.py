import sys
from pathlib import Path
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

try:
    from services.pipeline_service import ensure_database_schema
    from app.core.config import get_settings
    
    def run_init():
        settings = get_settings()
        logger.info(f"Initializing database schema for project: {settings.appwrite_project_id}")
        
        # Override the SKIP_SCHEMA_CHECK for this script
        os.environ["SKIP_SCHEMA_CHECK"] = "false"
        
        ensure_database_schema()
        logger.info("Database initialization complete.")

    if __name__ == "__main__":
        run_init()
except Exception as e:
    logger.error(f"Initialization failed: {e}")
    sys.exit(1)
