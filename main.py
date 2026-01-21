"""
Job Market Agent - CLI Entry Point
Automated job search and application pipeline.
"""

import os
import sys
import argparse
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Fix Windows Unicode Output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Local imports
from services.pipeline_service import JobApplicationPipeline, ensure_database_schema
from config import Config

# Load environment variables
load_dotenv()

# Polyfill API keys
if os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = os.getenv('GOOGLE_API_KEY')
if os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Job Market Agent - Automated Application Pipeline')
    parser.add_argument('--cv', type=str, help='Path to your CV (PDF, DOCX, or TXT)')
    parser.add_argument('--query', type=str, help='Job search query (e.g., "Python Developer")')
    parser.add_argument('--location', type=str, help='Job location (e.g., "Remote", "London")')
    parser.add_argument('--max-jobs', type=int, default=5, help='Maximum number of jobs to apply for')
    parser.add_argument('--template', type=str, choices=['modern', 'minimalist', 'academic'], default='modern', help='CV template to use')
    parser.add_argument('--ensure-schema', action='store_true', help='Ensure Appwrite database schema exists')
    
    args = parser.parse_args()

    # 1. Ensure Schema if requested
    if args.ensure_schema:
        ensure_database_schema()

    cv_path = args.cv or os.getenv('CV_FILE_PATH', 'cvs/CV.pdf')
    cv_path = str(Path(cv_path))
    if not Path(cv_path).exists():
        logger.error(f"CV not found at {cv_path}. Please provide a valid path with --cv or set CV_FILE_PATH.")
        sys.exit(1)
    query = args.query or os.getenv('SEARCH_QUERY', 'Python Developer')
    location = args.location or os.getenv('LOCATION', 'South Africa')
    
    # 3. Initialize Pipeline
    try:
        pipeline = JobApplicationPipeline(cv_path=cv_path)
        
        # 4. Run Pipeline
        pipeline.run(
            query=query,
            location=location,
            max_applications=args.max_jobs,
            template=args.template
        )
        
        # 5. Summary
        pipeline.print_summary()
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
