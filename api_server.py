import os
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

# Ensure GOOGLE_API_KEY is set for agno/Gemini BEFORE importing agents
if os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')
    print("✓ Polyfilled GOOGLE_API_KEY from GEMINI_API_KEY")

from flask import Flask, request, jsonify, send_file, g, Response
from flask_cors import CORS
import json
import re
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from main import JobApplicationPipeline
from utils.ai_retries import retry_ai_call
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.services.messaging import Messaging
from appwrite.id import ID
from appwrite.query import Query
from appwrite.input_file import InputFile
from functools import wraps
import uuid
import threading
from datetime import datetime
import threading
from datetime import datetime
import time
import tempfile
import traceback

# load_dotenv() already called at top


app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "running", 
        "message": "Job Market Agent API is active. If you are looking for the frontend, please ensure you are using the Docker Runtime or a separate frontend host."
    })

# Configure CORS for production
allowed_origins = os.getenv('CORS_ORIGINS', '').split(',')
default_origins = [
    'http://localhost:5173',
    'https://job-market-agent.vercel.app',
    'https://job-market-agent.onrender.com'
]
# Clean up and combine unique origins
active_origins = list(set([o.strip() for o in allowed_origins + default_origins if o.strip()]))
origin_patterns = active_origins + [r"^https://.*\.vercel\.app$"]

print(f"CORS Allowed Origins: {active_origins}")

CORS(app, resources={
    r"/api/*": {
        "origins": origin_patterns,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Appwrite-Project", "X-Appwrite-JWT"],
        "supports_credentials": True
    }
})

app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24)  # For session management
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Initialize Appwrite Client
client = Client()
client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
# client.set_key(os.getenv('APPWRITE_API_KEY')) # Only needed for admin tasks

# Configure upload folder
# Configure upload folder - Use temp dir for Render compatibility
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'job_market_agent_uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
    except Exception as e:
        print(f"Error creating upload folder {UPLOAD_FOLDER}: {e}")
        # Fallback to local
        UPLOAD_FOLDER = 'uploads'
        if not os.path.exists(UPLOAD_FOLDER):
             os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Appwrite Constants
DATABASE_ID = 'job-market-db'
COLLECTION_ID_JOBS = 'jobs'
COLLECTION_ID_APPLICATIONS = 'applications'
COLLECTION_ID_PROFILES = 'profiles'
BUCKET_ID_CVS = 'cv-bucket'
COLLECTION_ID_ANALYTICS = 'analytics'
COLLECTION_ID_MATCHES = 'matches'


# Global storage for pipelines and profiles (in production, use Redis or database)
import threading
store_lock = threading.Lock()
pipeline_store = {}
profile_store = {}

apply_jobs = {}
APPLY_JOB_TIMEOUT_SECS = 300
APPLY_JOB_CLEANUP_SECS = 600

rate_limits = {}

def check_rate(endpoint: str, limit: int, window_sec: int = 60):
    try:
        uid = getattr(g, 'user_id', None)
        if not uid:
            return True
        now = time.time()
        key = f"{uid}:{endpoint}"
        bucket = rate_limits.get(key, [])
        bucket = [t for t in bucket if now - t < window_sec]
        if len(bucket) >= limit:
            rate_limits[key] = bucket
            return False
        bucket.append(now)
        rate_limits[key] = bucket
        return True
    except Exception:
        return True

MAX_RATE_ANALYTICS_PER_MIN = 60
MAX_RATE_MATCHES_PER_MIN = 20
MAX_RATE_APPLY_PER_MIN = 5
MAX_RATE_ANALYZE_PER_MIN = 5

# Simple in-memory rate limiting


def _rehydrate_pipeline_from_profile(session_id: str, client) -> JobApplicationPipeline | None:
    try:
        databases = Databases(client)
        storage = Storage(client)
        
        try:
            existing_profiles = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                queries=[Query.equal('userId', session_id)]
            )
        except Exception as e:
            # Check if it's a "Collection not found" type error which implies we can't find anything
            print(f"Error listing documents for rehydration: {e}")
            return None

        if existing_profiles.get('total', 0) == 0:
            print(f"DEBUG: No profile found for user {session_id}")
            return None
        doc = existing_profiles['documents'][0]
        file_id = doc.get('cv_file_id') or doc.get('fileId')
        cv_text = doc.get('cv_text')
        
        print(f"DEBUG: Rehydrate - Found profile. file_id={file_id}, cv_text_len={len(cv_text) if cv_text else 0}")

        if cv_text:
            pipeline = JobApplicationPipeline()
            pipeline.build_profile(cv_text)
            with store_lock:
                pipeline_store[session_id] = pipeline
                profile_store[session_id] = {
                    'profile_data': parse_profile(pipeline.profile),
                    'raw_profile': pipeline.profile,
                    'cv_filename': doc.get('cv_filename', 'CV'),
                    'cv_content': cv_text,
                    'file_id': file_id
                }
            print("DEBUG: Rehydrated from cv_text")
            return pipeline
        
        # Fallback: If no text, try to download file
        if file_id:
            try:
                # Ensure upload folder exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                tmp_name = f"rehydrated_{file_id}.pdf"
                cv_path = os.path.join(app.config['UPLOAD_FOLDER'], tmp_name)
                
                # Download if not exists or force refresh logic could go here
                print(f"DEBUG: Downloading CV from storage: {file_id}")
                data = storage.get_file_download(bucket_id=BUCKET_ID_CVS, file_id=file_id)
                with open(cv_path, 'wb') as f:
                    f.write(data)
                
                if not os.path.exists(cv_path):
                     print("DEBUG: Download failed, file not at path")
                     return None

                print(f"DEBUG: Download successful to {cv_path}, size={os.path.getsize(cv_path)}")
                    
                pipeline = JobApplicationPipeline(cv_path=cv_path)
                cv_content = pipeline.load_cv()
                
                # Validation
                if not cv_content or "Extraction failed" in cv_content:
                     print(f"DEBUG: PDF extraction failed: {cv_content}")
                     return None

                pipeline.build_profile(cv_content)
                
                with store_lock:
                    pipeline_store[session_id] = pipeline
                    profile_store[session_id] = {
                        'profile_data': parse_profile(pipeline.profile),
                        'raw_profile': pipeline.profile,
                        'cv_filename': doc.get('cv_filename', 'CV'),
                        'cv_content': cv_content,
                        'file_id': file_id
                    }
                print("DEBUG: Rehydrated from file download")
                return pipeline
            except Exception as e:
                print(f"DEBUG: Error rehydrating from file: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        print("DEBUG: Rehydration failed - No text and no file_id")
        return None

    except Exception as e:
        print(f"Rehydrate pipeline error: {e}")
        return None

def ensure_database_schema():
    """
    Ensure all required Appwrite collections and attributes exist.
    Run this on startup.
    """
    try:
        from appwrite.permission import Permission
        from appwrite.role import Role

        api_key = os.getenv('APPWRITE_API_KEY')
        if not api_key:
            print("WARNING: APPWRITE_API_KEY not found. Schema checks skipped.")
            return

        admin_client = Client()
        admin_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
        admin_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        admin_client.set_key(api_key)
        admin_db = Databases(admin_client)

        def _ensure_collection(col_id, col_name, permissions=None):
            try:
                # 1. Check if exists
                try:
                    admin_db.get_collection(DATABASE_ID, col_id)
                except Exception as e:
                    code = getattr(e, 'code', 0)
                    if code == 404 or "404" in str(e) or "not found" in str(e).lower():
                        print(f"Creating collection {col_name} ({col_id})...")
                        # Create with Default Permissions (empty)
                        admin_db.create_collection(
                            DATABASE_ID, 
                            col_id, 
                            col_name,
                            permissions=permissions or [],
                            document_security=True
                        )
                        time.sleep(1) # Propagate
                    else:
                        raise e
                
                # 2. Update Permissions (Self-Validation)
                # Ensure document security is ON and Users have rights
                # We update it every time to ensure compliance
                if not permissions:
                     # Default: Users can create, read/update/delete THEIR OWN documents
                     permissions = [
                         Permission.create(Role.users()),
                         Permission.read(Role.users()),
                         Permission.update(Role.users()),
                         Permission.delete(Role.users())
                     ]
                
                try:
                    admin_db.update_collection(
                        DATABASE_ID,
                        col_id,
                        col_name,
                        permissions=permissions,
                        document_security=True,
                        enabled=True
                    )
                except Exception as pe:
                    print(f"Warning updating permissions for {col_name}: {pe}")

            except Exception as e:
                print(f"Error checking collection {col_name}: {e}")

        def _ensure_attr(col_id, key, type_, size=255, required=False, default=None, min_val=None, max_val=None):
            try:
                # 1. Check if attribute exists
                try:
                    # List attributes to check existence effectively
                    # This avoids the "Limit reached" error if we just blindly create
                    # Note: list_attributes might be paginated but usually we don't have > 25 attrs
                    attrs_list = admin_db.list_attributes(DATABASE_ID, col_id)
                    existing_keys = [a.get('key') for a in attrs_list.get('attributes', [])]
                    if key in existing_keys:
                        return # Exists, skip
                except Exception as le:
                    # If list fails, we might fall back to try-create
                    print(f"Warning listing attributes for {col_id}: {le}")

                # 2. Create if not exists
                if type_ == 'string':
                    try:
                        admin_db.create_string_attribute(DATABASE_ID, col_id, key, size, required, default)
                    except AttributeError:
                        admin_db.create_string_column(DATABASE_ID, col_id, key, size, required, default)
                elif type_ == 'integer':
                    try:
                        admin_db.create_integer_attribute(DATABASE_ID, col_id, key, required, min_val, max_val, default)
                    except AttributeError:
                        admin_db.create_integer_column(DATABASE_ID, col_id, key, required, min_val, max_val, default)
                elif type_ == 'boolean':
                    try:
                        admin_db.create_boolean_attribute(DATABASE_ID, col_id, key, required, default)
                    except AttributeError:
                        admin_db.create_boolean_column(DATABASE_ID, col_id, key, required, default)
            except Exception as e:
                msg = str(e).lower()
                if "already exists" in msg or getattr(e, 'code', 0) == 409:
                    pass 
                elif "limit" in msg:
                    print(f"Warning: Attribute limit reached for {key} in {col_id}.")
                else:
                    print(f"Error creating attribute {key} in {col_id}: {e}")

        # 1. Ensure Collections with Correct Permissions
        # Profiles: Users create own, read own
        _ensure_collection(COLLECTION_ID_PROFILES, 'Profiles')
        
        # Matches: Users create/read own
        _ensure_collection(COLLECTION_ID_MATCHES, 'Matches')
        
        # Analytics: Users create own
        _ensure_collection(COLLECTION_ID_ANALYTICS, 'Analytics')
        
        # Applications: Users create/read own
        _ensure_collection(COLLECTION_ID_APPLICATIONS, 'Applications')

        # 2. Profiles Attributes
        _ensure_attr(COLLECTION_ID_PROFILES, 'userId', 'string', 255, True)
        _ensure_attr(COLLECTION_ID_PROFILES, 'cv_file_id', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'cv_filename', 'string', 255, False)
        # Large text fields
        _ensure_attr(COLLECTION_ID_PROFILES, 'cv_text', 'string', 1000000, False) 
        _ensure_attr(COLLECTION_ID_PROFILES, 'skills', 'string', 10000, False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'strengths', 'string', 10000, False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'education', 'string', 5000, False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'experience_level', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'career_goals', 'string', 5000, False)
        
        # Preferences
        _ensure_attr(COLLECTION_ID_PROFILES, 'notification_enabled', 'boolean', required=False, default=False)
        _ensure_attr(COLLECTION_ID_PROFILES, 'notification_threshold', 'integer', required=False, min_val=0, max_val=100, default=70)
        _ensure_attr(COLLECTION_ID_PROFILES, 'updated_at', 'string', 64, False)

        # 3. Matches Attributes
        _ensure_attr(COLLECTION_ID_MATCHES, 'userId', 'string', 255, True)
        _ensure_attr(COLLECTION_ID_MATCHES, 'location', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_MATCHES, 'matches', 'string', 1000000, False) # Large JSON
        _ensure_attr(COLLECTION_ID_MATCHES, 'last_seen', 'string', 64, False)

        # 4. Analytics Attributes
        _ensure_attr(COLLECTION_ID_ANALYTICS, 'userId', 'string', 255, True)
        _ensure_attr(COLLECTION_ID_ANALYTICS, 'event', 'string', 255, True)
        _ensure_attr(COLLECTION_ID_ANALYTICS, 'properties', 'string', 10000, False)
        _ensure_attr(COLLECTION_ID_ANALYTICS, 'page', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_ANALYTICS, 'created_at', 'string', 64, False)

        # 5. Applications Attributes
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'userId', 'string', 255, True)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'jobTitle', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'company', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'jobUrl', 'string', 1000, False)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'location', 'string', 255, False)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'status', 'string', 50, False)
        _ensure_attr(COLLECTION_ID_APPLICATIONS, 'files', 'string', 5000, False)
        
        print("✓ Database schema ensured")

    except Exception as e:
        print(f"ensure_database_schema error: {e}")
        import traceback
        traceback.print_exc()

ensure_database_schema()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Create a new client instance for this request to be thread-safe
            # and to set the JWT for this specific user
            request_client = Client()
            request_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
            request_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
            request_client.set_jwt(token)
            
            account = Account(request_client)
            user = account.get()
            
            # Store user info in Flask's global 'g' object
            g.user = user
            g.user_id = user['$id']
            g.client = request_client # Pass the authenticated client for DB operations
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/search-jobs', methods=['POST'])
@login_required
def search_jobs():
    try:
        data = request.get_json()
        query = data.get('query', '')
        location = data.get('location', '')
        max_results = int(data.get('max_results', 10))
        
        # Initialize the pipeline
        pipeline = JobApplicationPipeline()
        
        # Search for jobs using pipeline API (query, location, max_results)
        jobs = pipeline.search_jobs(query=query or 'Python Developer', location=location or 'South Africa', max_results=max_results)
        
        # Format jobs for frontend
        formatted_jobs = []
        for job in jobs[:10]:  # Limit to 10 jobs
            formatted_jobs.append({
                'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'description': (job.get('description', '') or '')[:200] + ('...' if job.get('description') else ''),
                'url': job.get('url', ''),
            })
        
        return jsonify({'jobs': formatted_jobs})
    
    except Exception as e:
        print(f"Error searching jobs: {e}")
        return jsonify({'jobs': [], 'error': str(e)})

def _process_application_async(job_data, session_id, client_jwt_client, template_type=None):
    try:
        if session_id not in pipeline_store:
            pipeline_store[session_id] = JobApplicationPipeline()
        pipeline = pipeline_store[session_id]
        if not getattr(pipeline, 'cv_engine', None):
            profile_info = profile_store.get(session_id)
            if profile_info and profile_info.get('cv_content'):
                from utils.cv_tailoring import CVTailoringEngine
                pipeline.cv_engine = CVTailoringEngine(
                    profile_info['cv_content'],
                    profile_info.get('profile_data', {})
                )
                pipeline.profile = profile_info.get('profile_data', {})
            else:
                rehydrated = _rehydrate_pipeline_from_profile(session_id, client_jwt_client)
                if not rehydrated:
                    # Check if CV is available locally before attempting to load
                    if pipeline.cv_path and os.path.exists(pipeline.cv_path):
                         cv_content = pipeline.load_cv()
                         # pipeline.build_profile(cv_content) # Don't rebuild here, just load
                    else:
                         print(f"Error: No CV found for user {session_id} and rehydration failed.")
                         return {'error': 'CV not found. Please upload a CV first.'}
        app_result = pipeline.generate_application_package(job_data, template_type)
        if not app_result or not isinstance(app_result, dict):
            return {'error': 'Application generation failed. Please try a different template or re-upload your CV.'}
        interview_prep_path = pipeline.prepare_interview(job_data, output_dir=app_result.get('app_dir'))
        files_payload = {}
        try:
            databases = Databases(client_jwt_client)
            storage = Storage(client_jwt_client)
            cv_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['cv_path']))
            cl_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['cover_letter_path']))
            meta_upload = None
            if app_result.get('metadata_path'):
                meta_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['metadata_path']))
            prep_upload = None
            if interview_prep_path:
                prep_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(interview_prep_path))
            files_payload = {
                'cv': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={cv_upload['$id']}",
                'cover_letter': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={cl_upload['$id']}",
                'interview_prep': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={prep_upload['$id']}" if prep_upload else None,
                'metadata': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={meta_upload['$id']}" if meta_upload else None
            }
            databases.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_APPLICATIONS,
                document_id=ID.unique(),
                data={
                    'userId': session_id,
                    'jobTitle': job_data.get('title', 'Unknown'),
                    'company': job_data.get('company', 'Unknown'),
                    'jobUrl': job_data.get('url', ''),
                    'location': job_data.get('location', ''),
                    'status': 'applied',
                    'files': files_payload
                }
            )
        except Exception as e:
            print(f"Error saving application to DB: {e}")
        return {'files': files_payload, 'ats_score': app_result.get('ats_score'), 'ats_analysis': app_result.get('ats_analysis')}
    except Exception as e:
        print(f"Async apply error: {e}")
        return {'error': str(e)}

@app.route('/api/apply-job', methods=['POST'])
@login_required
def apply_job():
    try:
        if not check_rate('apply-job', MAX_RATE_APPLY_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        if request.is_json:
            data = request.get_json()
            session_id = g.user_id
            job_data = data.get('job')
            template_type = data.get('template')
            job_id = str(uuid.uuid4())
            apply_jobs[job_id] = {'status': 'processing', 'created_at': time.time()}
            client_jwt_client = g.client
            def _runner():
                result = _process_application_async(job_data, session_id, client_jwt_client, template_type)
                current = apply_jobs.get(job_id, {})
                if current.get('status') == 'cancelled':
                    return
                if 'error' in result:
                    apply_jobs[job_id] = {'status': 'error', 'error': result['error'], 'created_at': current.get('created_at', time.time())}
                else:
                    apply_jobs[job_id] = {
                        'status': 'done',
                        'files': result['files'],
                        'ats': {'score': result.get('ats_score'), 'analysis': result.get('ats_analysis')},
                        'created_at': current.get('created_at', time.time())
                    }
            threading.Thread(target=_runner, daemon=True).start()
            return jsonify({'success': True, 'job_id': job_id})
        return jsonify({'success': False, 'error': 'Invalid request'})
    except Exception as e:
        print(f"Error starting apply job: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/apply-status', methods=['GET'])
@login_required
def apply_status():
    try:
        job_id = request.args.get('job_id')
        if not job_id or job_id not in apply_jobs:
            return jsonify({'status': 'not_found'})
        info = apply_jobs[job_id]
        # Timeout processing jobs
        if info.get('status') == 'processing':
            created = info.get('created_at', time.time())
            if time.time() - created > APPLY_JOB_TIMEOUT_SECS:
                info = {'status': 'error', 'error': 'Job timed out. Please try again.'}
                apply_jobs[job_id] = info
        return jsonify(info)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

# Cleanup thread for apply_jobs
def _cleanup_apply_jobs():
    while True:
        try:
            now = time.time()
            to_delete = []
            for jid, info in list(apply_jobs.items()):
                created = info.get('created_at', now)
                if info.get('status') in ('done', 'error') and (now - created) > APPLY_JOB_CLEANUP_SECS:
                    to_delete.append(jid)
            for jid in to_delete:
                del apply_jobs[jid]
        except Exception:
            pass
        time.sleep(60)

threading.Thread(target=_cleanup_apply_jobs, daemon=True).start()

@app.route('/api/download', methods=['GET'])
def download_file():
    try:
        file_path = request.args.get('path')
        if not file_path:
             return jsonify({'error': 'File not found'}), 404
             
        # Security: Prevent path traversal
        file_path = os.path.normpath(file_path)
        if '..' in file_path or file_path.startswith(('/', '\\')):
             return jsonify({'error': 'Invalid path'}), 400
             
        # Only allow downloads from certain directories logic if needed, 
        # but for now ensuring no traversal is key. 
        # Ideally check if it's inside UPLOAD_FOLDER or artifacts.
        abs_path = os.path.abspath(file_path)
        upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
        
        # Determine if safe
        # (Assuming file_path passed from frontend is relative to some root or is a filename)
        # If it's a full path from DB, we need to be careful.
        # Given existing usage: return send_file(file_path)
        
        if not os.path.exists(file_path):
             return jsonify({'error': 'File not found'}), 404

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    try:
        databases = Databases(g.client)
        try:
            page = int(request.args.get('page', '1'))
            limit = int(request.args.get('limit', '10'))
        except Exception:
            page, limit = 1, 10
        offset = max(0, (page - 1) * limit)
        
        # Query applications for the current user
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_APPLICATIONS,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt'),
                Query.limit(limit),
                Query.offset(offset)
            ]
        )
        
        applications = []
        for doc in result['documents']:
            applications.append({
                'id': doc['$id'],
                'jobTitle': doc.get('jobTitle', 'Unknown Position'),
                'company': doc.get('company', 'Unknown Company'),
                'jobUrl': doc.get('jobUrl', ''),
                'location': doc.get('location', ''),
                'status': doc.get('status', 'applied'),
                'appliedDate': doc.get('$createdAt', '').split('T')[0], # Format date
                'files': doc.get('files')
            })
            
        return jsonify({'applications': applications, 'page': page, 'limit': limit, 'total': result.get('total', len(applications))})
    
    except Exception as e:
        print(f"Error getting applications: {e}")
        # Fallback to empty list or handle error gracefully
        return jsonify({'applications': [], 'error': str(e)})

@app.route('/api/analyze-cv', methods=['POST'])
@login_required
def analyze_cv():
    """Analyze uploaded CV and build candidate profile"""
    try:
        if not check_rate('analyze-cv', MAX_RATE_ANALYZE_PER_MIN):
             return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429

        cv_file = request.files.get('cv')
        if not cv_file:
            return jsonify({'success': False, 'error': 'Missing file'})
        
        if cv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Basic MIME/type validation
        allowed_mimes = {'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        content_type = cv_file.mimetype or ''
        if content_type not in allowed_mimes:
            return jsonify({'success': False, 'error': 'Invalid file type. Use PDF, DOC, or DOCX.'}), 400

        if cv_file and allowed_file(cv_file.filename):
            filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cv_file.save(cv_path)
            
            # Initialize the pipeline
            pipeline = JobApplicationPipeline(cv_path=cv_path)
            
            # Load CV
            cv_content = pipeline.load_cv()
            if not cv_content:
                return jsonify({'success': False, 'error': 'Failed to load CV'})
            
            # Build profile using AI
            # Ensure API keys are set (redundant check)
            if os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
                os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')
                
            profile_text = pipeline.build_profile(cv_content)
            
            if not profile_text:
                # Check if there was an error logged in the pipeline
                return jsonify({'success': False, 'error': 'Failed to build profile. Check server logs for details.'})
            
            # Parse profile text to extract structured data
            profile_data = parse_profile(profile_text)
            
            # --- Appwrite Integration ---
            try:
                databases = Databases(g.client)
                storage = Storage(g.client)
                
                # 1. Upload CV to Storage using InputFile
                from appwrite.input_file import InputFile
                
                result = storage.create_file(
                    bucket_id=BUCKET_ID_CVS,
                    file_id=ID.unique(),
                    file=InputFile.from_path(cv_path)
                )
                file_id = result['$id']

                # 2. Save Profile to Database
                # Check if profile already exists for this user
                existing_profiles = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                
                profile_doc_data = {
                    'userId': g.user_id,
                    'skills': json.dumps(profile_data.get('skills', [])),
                    'experience_level': profile_data.get('experience_level', 'N/A'),
                    'education': profile_data.get('education', ''),
                    'strengths': json.dumps(profile_data.get('strengths', [])),
                    'career_goals': profile_data.get('career_goals', ''),
                    'cv_file_id': file_id,
                    'cv_filename': filename,
                    'cv_text': cv_content
                }

                if existing_profiles['total'] > 0:
                    # Update existing profile
                    profile_id = existing_profiles['documents'][0]['$id']
                    databases.update_document(
                        database_id=DATABASE_ID,
                        collection_id=COLLECTION_ID_PROFILES,
                        document_id=profile_id,
                        data=profile_doc_data
                    )
                    print(f"DEBUG: Updated existing profile {profile_id} for user {g.user_id}")
                else:
                    # Create new profile
                    databases.create_document(
                        database_id=DATABASE_ID,
                        collection_id=COLLECTION_ID_PROFILES,
                        document_id=ID.unique(),
                        data=profile_doc_data
                    )
                    print(f"DEBUG: Created new profile for user {g.user_id}")
                
                # Update memory store immediately
                with store_lock:
                    profile_store[g.user_id] = {
                        'profile_data': profile_data,
                        'raw_profile': profile_text,
                        'cv_filename': filename,
                        'cv_content': cv_content,
                        'file_id': file_id
                    }
                print("DEBUG: Profile store updated in memory")

                # In a stateless architecture, we'd rebuild it from the stored data
                # For now, we'll keep the session_id concept for the immediate session
                # but rely on DB for persistence.
                session_id = g.user_id # Use user_id as session_id for simplicity in this flow
                with store_lock:
                    pipeline_store[session_id] = pipeline
                    profile_store[session_id] = {
                        'profile_data': profile_data,
                        'raw_profile': profile_text,
                        'cv_filename': filename,
                        'cv_content': cv_content,
                        'file_id': file_id 
                    }

            except Exception as db_error:
                print(f"Appwrite Error: {db_error}")
                # Continue even if DB save fails, to return result to user
                # But in production you'd want to handle this better
            
            # Clean up local file
            # os.remove(cv_path) # Keep for now if pipeline needs it, or ensure pipeline loads content into memory

            return jsonify({
                'success': True,
                'session_id': g.user_id, # Return user_id as session_id
                'profile': profile_data,
                'raw_profile': profile_text,
                'cv_filename': filename
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        print(f"Error analyzing CV: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/match-jobs', methods=['POST'])
@login_required
def match_jobs():
    """Find and rank jobs based on CV profile"""
    try:
        if not check_rate('match-jobs', MAX_RATE_MATCHES_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        data = request.get_json()
        # session_id is now effectively user_id
        session_id = g.user_id 
        location = data.get('location', 'South Africa')
        max_results = int(data.get('max_results', 20))
        use_demo = bool(data.get('use_demo', False))
        
        profile_info = None
        
        # 0. Try cache in database if available and recent
        try:
            databases = Databases(g.client)
            cached = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_MATCHES,
                queries=[
                    Query.equal('userId', g.user_id),
                    Query.equal('location', location),
                    Query.limit(10)
                ]
            )
            if cached.get('total', 0) > 0 and not use_demo:
                docs = cached.get('documents', [])
                try:
                    docs.sort(key=lambda d: d.get('$createdAt', ''), reverse=True)
                except Exception:
                    pass
                doc = docs[0]
                created = doc.get('$createdAt')
                if created:
                    from datetime import datetime, timezone
                    try:
                        ts = datetime.fromisoformat(created.replace('Z', '+00:00')).timestamp()
                        if time.time() - ts < 900:
                            matches = json.loads(doc.get('matches', '[]') or '[]')
                            return jsonify({'success': True, 'matches': matches, 'cached': True})
                    except Exception:
                        pass
        except Exception as e:
            print(f"Cache read error: {e}")

        # 1. Try to get from memory first
        if session_id in profile_store:
            profile_info = profile_store[session_id]
        
        # 2. If not in memory, try to fetch from Appwrite DB
        if not profile_info:
            try:
                databases = Databases(g.client)
                existing_profiles = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                
                if existing_profiles.get('total', 0) > 0:
                    doc = existing_profiles.get('documents', [None])[0]
                    if not doc:
                        raise Exception('Profile document missing')
                    skills_raw = doc.get('skills', '[]')
                    strengths_raw = doc.get('strengths', '[]')
                    try:
                        skills_val = json.loads(skills_raw) if isinstance(skills_raw, str) else (skills_raw or [])
                    except Exception:
                        skills_val = []
                    try:
                        strengths_val = json.loads(strengths_raw) if isinstance(strengths_raw, str) else (strengths_raw or [])
                    except Exception:
                        strengths_val = []
                    profile_data = {
                        'skills': skills_val or [],
                        'experience_level': doc.get('experience_level', '') or '',
                        'education': doc.get('education', '') or '',
                        'strengths': strengths_val or [],
                        'career_goals': doc.get('career_goals', '') or ''
                    }
                    
                    # Reconstruct profile_info structure
                    profile_info = {
                        'profile_data': profile_data,
                        'raw_profile': '',
                        'cv_filename': doc.get('cv_filename', 'Stored Profile'),
                        'cv_content': doc.get('cv_text', ''),
                        'file_id': doc.get('cv_file_id')
                    }
                    
                    # Cache back to memory
                    profile_store[session_id] = profile_info
                    
            except Exception as e:
                print(f"Error fetching profile from DB: {e}")

        if not profile_info:
            return jsonify({'success': False, 'error': 'No profile found. Please upload CV first.'})
        
        # Ensure pipeline exists
        with store_lock:
            pipeline = pipeline_store.get(session_id)
            if not pipeline:
                pass
        
        if not pipeline:
            pipeline = _rehydrate_pipeline_from_profile(session_id, g.client)
            if not pipeline:
                pipeline = JobApplicationPipeline()
            with store_lock:
                pipeline_store[session_id] = pipeline
        
        # Extract skills from profile to build search query
        profile_data = profile_info['profile_data']
        skills = profile_data.get('skills', [])
        
        # Build search query from top skills
        search_query = ' '.join(skills[:3]) if skills else 'Software Developer'
        
        print(f"\n=== Job Matching ===")
        print(f"Search query: {search_query}")
        print(f"Location: {location}")
        
        if use_demo:
            jobs = []
        else:
            jobs = pipeline.search_jobs(
                query=search_query,
                location=location,
                max_results=max_results
            )

        # Fallback: broaden query if no results
        if not jobs:
            fallback_queries = [
                'Python Developer',
                'Software Engineer',
                'Software Developer'
            ]
            for fq in fallback_queries:
                if use_demo:
                    jobs = []
                else:
                    jobs = pipeline.search_jobs(
                        query=fq,
                        location=location,
                        max_results=max_results
                    )
                if jobs:
                    break
            # Final fallback: synthetic jobs derived from skills
            if not jobs:
                synthetic = []
                for skill in (skills[:3] or ['Software Developer']):
                    synthetic.append({
                        'title': f"{skill} Engineer",
                        'company': 'TopTech Co.',
                        'location': location,
                        'url': '',
                        'description': f"Role focusing on {skill}. Work with a modern stack and collaborative team.",
                    })
                jobs = synthetic
        
        print(f"Found {len(jobs)} jobs, scoring matches...")
        
        # Score and rank jobs based on profile match
        matches = []
        for job in jobs[:max_results]:
            match_result = score_job_match(job, profile_info)
            
            # Better location handling with fallbacks
            job_location = (
                job.get('location') or 
                job.get('job_location') or 
                job.get('city') or 
                ''
            )
            
            # Replace placeholder values with search location
            if not job_location or job_location in ['Unknown Location', 'N/A', 'unknown', '']:
                job_location = location
            
            matches.append({
                'job': {
                    'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                    'title': job.get('title', 'Unknown Position'),
                    'company': job.get('company', 'Unknown Company'),
                    'location': job_location,
                    'description': job.get('description', 'No description available'),
                    'url': job.get('url', ''),
                },
                'match_score': match_result['score'],
                'match_reasons': match_result['reasons']
            })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"Returning {len(matches)} matched jobs")
        
        # Send email notification for high-quality matches honoring user preferences
        try:
            account = Account(g.client)
            user_account = account.get()
            user_email = user_account['email']
            user_name = user_account['name'] or 'there'

            notify_enabled = False
            notify_threshold = 70
            try:
                databases = Databases(g.client)
                prefs = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                if prefs['total'] > 0:
                    doc = prefs['documents'][0]
                    notify_enabled = bool(doc.get('notification_enabled', False))
                    notify_threshold = int(doc.get('notification_threshold', 70))
            except Exception as _pref_err:
                print(f"Preferences fetch failed, using defaults: {_pref_err}")

            if notify_enabled:
                send_job_match_notification(user_email, user_name, matches, threshold=notify_threshold)
        except Exception as notify_error:
            print(f"Note: Email notification skipped - {notify_error}")
        
        # Persist matches for caching
        try:
            databases = Databases(g.client)
            databases.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_MATCHES,
                document_id=ID.unique(),
                data={
                    'userId': g.user_id,
                    'location': location,
                    'matches': json.dumps(matches) # matches is already a list of dicts
                }
            )
        except Exception as e:
            print(f"Cache write error: {e}")
        return jsonify({
            'success': True,
            'matches': matches,
            'cached': False
        })
    
    except Exception as e:
        print(f"Error matching jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
@login_required
def get_profile():
    """Retrieve analyzed profile"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in profile_store:
            return jsonify({'success': False, 'error': 'No profile found'})
        
        profile_info = profile_store[session_id]
        
        return jsonify({
            'success': True,
            'profile': profile_info['profile_data'],
            'raw_profile': profile_info['raw_profile'],
            'cv_filename': profile_info['cv_filename']
        })
    
    except Exception as e:
        print(f"Error getting profile: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user_id = g.user_id
        
        # Validate profile data
        if not data:
            return jsonify({'success': False, 'error': 'No profile data provided'}), 400
        
        # Update profile in Appwrite
        try:
            databases = Databases(g.client)
            # Check if profile exists
            existing_profiles = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                queries=[
                    Query.equal('userId', user_id)
                ]
            )
            
            profile_doc = {
                'userId': user_id,
                'skills': json.dumps(data.get('skills', [])),
                'experience_level': data.get('experience_level', ''),
                'education': data.get('education', ''),
                'strengths': json.dumps(data.get('strengths', [])),
                'career_goals': data.get('career_goals', ''),
                'notification_enabled': bool(data.get('notification_enabled', False)),
                'notification_threshold': int(data.get('notification_threshold', 70)),
                'updated_at': datetime.now().isoformat()
            }
            
            if existing_profiles['total'] > 0:
                # Update existing profile
                doc_id = existing_profiles['documents'][0]['$id']
                databases.update_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    document_id=doc_id,
                    data=profile_doc
                )
            else:
                # Create new profile
                databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    document_id=ID.unique(),
                    data=profile_doc
                )
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except Exception as db_error:
            print(f"Database error updating profile: {db_error}")
            return jsonify({'success': False, 'error': 'Failed to update profile in database'}), 500
            
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/profile/current', methods=['GET'])
@login_required
def get_current_profile():
    try:
        databases = Databases(g.client)
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.limit(10)
            ]
        )
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
        docs = result.get('documents', [])
        try:
            docs.sort(key=lambda d: d.get('$updatedAt', d.get('$createdAt', '')), reverse=True)
        except Exception:
            pass
        doc = docs[0]
        filename = doc.get('cv_filename') or 'Unknown'
        uploaded = doc.get('$updatedAt') or doc.get('$createdAt')
        file_id = doc.get('cv_file_id')
        return jsonify({'success': True, 'cv_filename': filename, 'uploaded_at': uploaded, 'file_id': file_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/structured', methods=['GET'])
@login_required
def get_structured_profile():
    try:
        databases = Databases(g.client)
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.limit(10)
            ]
        )
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
        docs = result.get('documents', [])
        try:
            docs.sort(key=lambda d: d.get('$updatedAt', d.get('$createdAt', '')), reverse=True)
        except Exception:
            pass
        doc = docs[0]
        def _safe_json(field, default):
            try:
                v = doc.get(field)
                if isinstance(v, str):
                    import json
                    return json.loads(v)
                return v if v is not None else default
            except Exception:
                return default
        profile = {
            'skills': _safe_json('skills', []),
            'experience_level': doc.get('experience_level', ''),
            'education': doc.get('education', ''),
            'strengths': _safe_json('strengths', []),
            'career_goals': doc.get('career_goals', ''),
        }
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def send_job_match_notification(user_email, user_name, matches, threshold=70):
    """
    Send email notification for high-quality job matches using Appwrite Messaging
    
    Args:
        user_email: User's email address
        user_name: User's name
        matches: List of matched jobs with scores
        threshold: Minimum match score to notify (default 70%)
    """
    try:
        # Filter high-quality matches
        high_quality_matches = [m for m in matches if m['match_score'] >= threshold]
        
        if not high_quality_matches:
            print(f"No matches above {threshold}% threshold for {user_email}")
            return
        
        # Sort by score (highest first)
        high_quality_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit to top 5 matches for email
        top_matches = high_quality_matches[:5]
        
        # Build email content
        email_subject = f"🎯 {len(high_quality_matches)} New Job Matches Found!"
        
        # Create HTML email body
        matches_html = ""
        for match in top_matches:
            job = match['job']
            score = match['match_score']
            reasons = match['match_reasons'][:3]  # Top 3 reasons
            
            # Color code based on score
            if score >= 80:
                badge_color = "#10b981"  # green
            elif score >= 70:
                badge_color = "#f59e0b"  # yellow
            else:
                badge_color = "#6b7280"  # gray
            
            matches_html += f"""
            <div style="background: #f9fafb; border-left: 4px solid {badge_color}; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #111827; font-size: 18px;">{job['title']}</h3>
                    <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 14px;">{score}% Match</span>
                </div>
                <p style="color: #6b7280; margin: 5px 0;">{job['company']} • {job['location']}</p>
                <div style="margin-top: 10px;">
                    <p style="font-weight: 600; color: #374151; margin-bottom: 5px;">Why this matches:</p>
                    <ul style="margin: 0; padding-left: 20px; color: #6b7280;">
                        {''.join([f"<li>{reason}</li>" for reason in reasons])}
                    </ul>
                </div>
                <a href="{job['url']}" style="display: inline-block; margin-top: 15px; background: linear-gradient(to right, #2563eb, #7c3aed); color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600;">View Job Details</a>
            </div>
            """
        
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(to right, #2563eb, #7c3aed); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">✨ Job Market Agent</h1>
                <p style="color: #e0e7ff; margin: 10px 0 0 0;">AI-Powered Career Matching</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #111827; margin-top: 0;">Hi {user_name}! 👋</h2>
                <p style="color: #6b7280; font-size: 16px;">Great news! We found <strong>{len(high_quality_matches)} high-quality job matches</strong> that align with your profile and career goals.</p>
                
                <div style="margin: 30px 0;">
                    {matches_html}
                </div>
                
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 20px; border-radius: 8px; margin-top: 30px;">
                    <p style="margin: 0; color: #1e40af; font-size: 14px;">
                        💡 <strong>Tip:</strong> Jobs with 80%+ match scores are excellent fits for your skills and experience. We recommend applying to these first!
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 14px; margin: 0;">
                        You're receiving this email because you have notifications enabled in your Job Market Agent profile.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email via Appwrite Messaging
        try:
            messaging = Messaging(client)
            
            # Create email message
            # Note: This requires an email provider to be configured in Appwrite console
            message = messaging.create_email(
                message_id=ID.unique(),
                subject=email_subject,
                content=email_body,
                topics=[],  # Can use topics for user segmentation
                users=[],   # Will send to specific email instead
                targets=[user_email],  # Direct email
                draft=False,
                html=True
            )
            
            print(f"✅ Email notification sent to {user_email} for {len(high_quality_matches)} matches")
            return True
            
        except Exception as email_error:
            # Graceful degradation - log error but don't fail job matching
            print(f"⚠️  Failed to send email notification: {email_error}")
            print(f"   This is likely because no email provider is configured in Appwrite console")
            print(f"   Job matching will continue normally")
            return False
            
    except Exception as e:
        print(f"Error in send_job_match_notification: {e}")
        return False

@app.route('/api/storage/download', methods=['GET'])
@login_required
def storage_download():
    try:
        bucket_id = request.args.get('bucket_id')
        file_id = request.args.get('file_id')
        if not bucket_id or not file_id:
            return jsonify({'error': 'Missing bucket_id or file_id'}), 400

        endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
        project_id = os.getenv('APPWRITE_PROJECT_ID')
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        if not project_id or not token:
            return jsonify({'error': 'Storage download unavailable'}), 500

        url = f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/download"
        headers = {
            'X-Appwrite-Project': project_id,
            'X-Appwrite-JWT': token
        }
        import requests as _req
        r = _req.get(url, headers=headers, stream=True)
        if r.status_code != 200:
            return jsonify({'error': 'Failed to fetch file'}), r.status_code
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), headers={'Content-Type': 'application/octet-stream'})
    except Exception as e:
        print(f"Error in storage_download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['POST'])
@login_required
def analytics():
    try:
        if not check_rate('analytics', MAX_RATE_ANALYTICS_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        data = request.get_json() or {}
        event = data.get('event')
        properties = data.get('properties', {})
        page = data.get('page')
        if not event:
            return jsonify({'success': False, 'error': 'Missing event'}), 400
        try:
            databases = Databases(g.client)
            databases.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_ANALYTICS,
                document_id=ID.unique(),
                data={
                    'userId': g.user_id,
                    'event': event,
                    'properties': json.dumps(properties),
                    'page': page or '',
                    'created_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Analytics write error: {e}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/matches/last', methods=['GET'])
@login_required
def matches_last():
    try:
        databases = Databases(g.client)
        location = request.args.get('location')
        queries = [
            Query.equal('userId', g.user_id),
            Query.limit(10)
        ]
        if location:
            queries.insert(1, Query.equal('location', location))
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_MATCHES,
            queries=queries
        )
        if not result or result.get('total', 0) == 0:
            return jsonify({'success': True, 'matches': [], 'cached': False})
        docs = result.get('documents', [])
        try:
            docs.sort(key=lambda d: d.get('$createdAt', ''), reverse=True)
        except Exception:
            pass
        doc = docs[0]
        matches_str = doc.get('matches', '[]') or '[]'
        matches = json.loads(matches_str)
        if matches is None:
            matches = []
        last_seen = datetime.now().isoformat()
        try:
            databases.update_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_MATCHES,
                document_id=doc['$id'],
                data={'last_seen': last_seen}
            )
        except Exception as e:
            print(f"Last seen update failed: {e}")
        return jsonify({
            'success': True,
            'matches': matches,
            'location': doc.get('location', ''),
            'created_at': doc.get('$createdAt'),
            'last_seen': last_seen,
            'cached': True
        })
    except Exception as e:
        print(f"Error in matches_last: {e}")
        try:
            return jsonify({'success': True, 'matches': [], 'cached': False})
        except Exception:
            return jsonify({'success': False, 'error': 'Failed to fetch last matches'}), 200

def parse_profile(profile_output):
    profile_data = {'skills': [], 'experience_level': '', 'education': '', 'strengths': [], 'career_goals': '', 'name': '', 'email': '', 'phone': '', 'location': '', 'links': {'linkedin': '', 'github': '', 'portfolio': ''}}

    try:
        if isinstance(profile_output, dict):
            skills_val = profile_output.get('skills', [])
            strengths_val = profile_output.get('strengths', [])
            experience_val = profile_output.get('experience_level', '')
            education_val = profile_output.get('education', '')
            career_val = profile_output.get('career_goals', '')
            name_val = profile_output.get('name', '')
            email_val = profile_output.get('email', '')
            phone_val = profile_output.get('phone', '')
            location_val = profile_output.get('location', '')
            links_val = profile_output.get('links', {})

            if isinstance(skills_val, str):
                skills_val = [s.strip() for s in skills_val.split(',') if s.strip()]
            if isinstance(strengths_val, str):
                strengths_val = [s.strip() for s in strengths_val.split(',') if s.strip()]
            if isinstance(links_val, dict):
                profile_data['links'] = {'linkedin': links_val.get('linkedin', ''), 'github': links_val.get('github', ''), 'portfolio': links_val.get('portfolio', '')}

            profile_data['skills'] = skills_val or []
            profile_data['strengths'] = strengths_val or []
            profile_data['experience_level'] = experience_val or ''
            profile_data['education'] = education_val or ''
            profile_data['career_goals'] = career_val or ''
            profile_data['name'] = name_val or ''
            profile_data['email'] = email_val or ''
            profile_data['phone'] = phone_val or ''
            profile_data['location'] = location_val or ''
            return profile_data

        if isinstance(profile_output, list):
            if len(profile_output) == 1 and isinstance(profile_output[0], dict):
                return parse_profile(profile_output[0])
            profile_text = json.dumps(profile_output)
        elif isinstance(profile_output, bytes):
            profile_text = profile_output.decode('utf-8', errors='ignore')
        else:
            profile_text = str(profile_output)

        json_str = profile_text
        if '```json' in profile_text:
            json_str = profile_text.split('```json')[1].split('```')[0]
        elif '```' in profile_text:
            json_str = profile_text.split('```')[1].split('```')[0]

        json_str = json_str.strip()
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return parse_profile(data)
        except Exception:
            pass

        skills_block_match = re.search(r'(?:Skills|Technical Skills|Expertise|Core Competencies)[:\s]*([\s\S]*?)(?=\n{2,}|\n[A-Z][A-Za-z ]{2,}\n|$)', profile_text, re.IGNORECASE)
        if skills_block_match:
            skills_text = skills_block_match.group(1)
            tokens = re.findall(r'([A-Za-z][A-Za-z0-9+#\.\-\s]{2,})', skills_text)
            cleaned = []
            for t in tokens:
                tt = t.strip()
                if tt and tt.lower() not in ('skills', 'technical skills', 'expertise', 'core competencies'):
                    cleaned.append(tt)
            parts = []
            for c in cleaned:
                for p in re.split(r'[,;/]|•|\n', c):
                    ps = p.strip()
                    if ps and len(ps) > 2:
                        parts.append(ps)
            uniq = []
            seen = set()
            for p in parts:
                key = p.lower()
                if key not in seen:
                    seen.add(key)
                    uniq.append(p)
            profile_data['skills'] = uniq[:20]

        exp_match = re.search(r'(?:Experience Level|Experience|Years)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
        if exp_match:
            profile_data['experience_level'] = exp_match.group(1).strip()

        edu_block_match = re.search(r'(?:Education|Qualifications|Degrees)[:\s]*([\s\S]*?)(?=\n{2,}|\n[A-Z][A-Za-z ]{2,}\n|$)', profile_text, re.IGNORECASE)
        if edu_block_match:
            profile_data['education'] = edu_block_match.group(1).strip()

        strengths_match = re.search(r'(?:Strengths|Key Strengths)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\n[A-Z]|$)', profile_text, re.IGNORECASE)
        if strengths_match:
            strengths_text = strengths_match.group(1)
            strengths = re.findall(r'(?:[-•*]\s*)?([^\n,;]+)', strengths_text)
            profile_data['strengths'] = [s.strip() for s in strengths if len(s.strip()) > 5][:5]

        goals_match = re.search(r'(?:Career Goals|Goals|Aspirations)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
        if goals_match:
            profile_data['career_goals'] = goals_match.group(1).strip()

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", profile_text)
        if email_match:
            profile_data['email'] = email_match.group(0)
        phone_match = re.search(r"(\+?\d[\d\s\-]{7,}\d)", profile_text)
        if phone_match:
            profile_data['phone'] = phone_match.group(0)
        loc_match = re.search(r"(?:Location|Address)[:\s]*([^\n]+)", profile_text, re.IGNORECASE)
        if loc_match:
            profile_data['location'] = loc_match.group(1).strip()
        else:
            city_match = re.search(r"\b(Cape Town|Johannesburg|Pretoria|Durban|Sandton|South Africa|Gauteng|Western Cape)\b", profile_text, re.IGNORECASE)
            if city_match:
                profile_data['location'] = city_match.group(0)
        linkedin_match = re.search(r"(https?://[^\s]*linkedin\.com[^\s]*)", profile_text, re.IGNORECASE)
        if linkedin_match:
            profile_data['links']['linkedin'] = linkedin_match.group(1)
        github_match = re.search(r"(https?://[^\s]*github\.com[^\s]*)", profile_text, re.IGNORECASE)
        if github_match:
            profile_data['links']['github'] = github_match.group(1)
        portfolio_match = re.search(r"(https?://[^\s]*(portfolio|behance|dribbble|personal)[^\s]*)", profile_text, re.IGNORECASE)
        if portfolio_match:
            profile_data['links']['portfolio'] = portfolio_match.group(1)
        name_candidate = ''
        lines = [l.strip() for l in profile_text.splitlines() if l.strip()]
        if lines:
            for l in lines[:5]:
                ll = l.lower()
                if '@' in l or 'linkedin' in ll or 'github' in ll or 'curriculum vitae' in ll:
                    continue
                if len(l.split()) <= 5:
                    name_candidate = l
                    break
            profile_data['name'] = name_candidate

    except Exception as e:
        print(f"Error parsing profile: {e}")

    return profile_data

def score_job_match(job, profile_info):
    """Score how well a job matches the candidate profile"""
    profile_data = profile_info['profile_data']
    job_title = job.get('title', '').lower()
    job_description = (job.get('description', '') or '').lower()
    job_company = job.get('company', '').lower()
    
    # Combine all job text for better matching
    job_text = f"{job_title} {job_description} {job_company}"
    
    score = 20  # Base score - gives credit for being in search results
    reasons = []
    
    # Debug output
    print(f"\n=== Scoring: {job.get('title', 'Unknown')} ===")
    
    # Check skill matches (more flexible matching)
    skills = profile_data.get('skills', [])
    matched_skills = []
    
    for skill in skills:
        skill_lower = skill.lower()
        skill_words = [w for w in skill_lower.split() if len(w) > 2]
        
        # Try exact match first
        if skill_lower in job_text:
            matched_skills.append(skill)
            score += 15
            print(f"  ✓ Exact skill: {skill}")
        # Try partial match (any significant word from skill)
        elif any(word in job_text for word in skill_words):
            matched_skills.append(skill)
            score += 10
            print(f"  ✓ Partial skill: {skill}")
    
    if matched_skills:
        reasons.append(f"Matches your skills: {', '.join(matched_skills[:3])}")
    
    # Check experience level alignment
    experience = profile_data.get('experience_level', '').lower()
    if experience:
        if 'senior' in experience and 'senior' in job_text:
            score += 15
            reasons.append("Senior level match")
        elif 'junior' in experience and ('junior' in job_text or 'entry' in job_text):
            score += 15
            reasons.append("Junior/Entry level match")
        elif 'mid' in experience and ('mid' in job_text or 'intermediate' in job_text):
            score += 15
            reasons.append("Mid-level match")
        else:
            score += 5  # General experience consideration
    
    # Check strengths alignment
    strengths = profile_data.get('strengths', [])
    for strength in strengths[:2]:  # Check top 2 strengths
        strength_words = [w for w in strength.lower().split() if len(w) > 3]
        if any(word in job_text for word in strength_words):
            score += 8
            reasons.append(f"Leverages {strength}")
            print(f"  ✓ Strength: {strength}")
    
    # Check career goals
    goals = profile_data.get('career_goals', '').lower()
    if goals:
        goal_words = [w for w in goals.split() if len(w) > 3]
        if any(word in job_text for word in goal_words):
            score += 10
            reasons.append("Aligns with career goals")
    
    # Ensure score is between 0-100
    score = min(score, 100)
    
    print(f"  Score: {score}")
    
    # Add default reason if no specific reasons found
    if not reasons:
        reasons.append("Relevant to your profile")
    
    return {
        'score': score,
        'reasons': reasons[:3]
    }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'success': False, 'error': 'File too large. Max 10MB.'}), 413
@app.route('/api/apply-cancel', methods=['POST'])
@login_required
def apply_cancel():
    try:
        job_id = request.args.get('job_id') or (request.get_json() or {}).get('job_id')
        if not job_id or job_id not in apply_jobs:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        info = apply_jobs[job_id]
        info['status'] = 'cancelled'
        apply_jobs[job_id] = info
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/applications/<doc_id>/status', methods=['PUT'])
@login_required
def update_application_status(doc_id):
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        allowed = {'pending', 'applied', 'interview', 'rejected'}
        if new_status not in allowed:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400

        databases = Databases(g.client)
        doc = databases.get_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_APPLICATIONS,
            document_id=doc_id
        )
        if doc.get('userId') != g.user_id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403

        databases.update_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_APPLICATIONS,
            document_id=doc_id,
            data={'status': new_status}
        )
        return jsonify({'success': True})
    except Exception as e:
        print(f"Update application status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/apply-preview', methods=['POST'])
@login_required
def apply_preview():
    try:
        if not check_rate('apply-job', MAX_RATE_APPLY_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        data = request.get_json()
        job_data = data.get('job')
        template_type = (data.get('template') or 'MODERN').lower()
        if not isinstance(job_data, dict):
            return jsonify({'success': False, 'error': 'Missing job data'}), 400

        with store_lock:
            if g.user_id not in pipeline_store:
                pipeline_store[g.user_id] = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            
            pipeline = pipeline_store[g.user_id]
            if not pipeline:
                 pipeline = JobApplicationPipeline()
                 pipeline_store[g.user_id] = pipeline
        if not getattr(pipeline, 'cv_engine', None):
            profile_info = profile_store.get(g.user_id)
            if profile_info and profile_info.get('cv_content'):
                from utils.cv_tailoring import CVTailoringEngine
                pipeline.cv_engine = CVTailoringEngine(profile_info['cv_content'], profile_info.get('profile_data', {}))
                pipeline.profile = profile_info.get('profile_data', {})
            else:
                # If we have no CV content in store and no rehydration possible, we cannot proceed.
                # Do NOT fallback to load_cv() which defaults to 'cvs/CV.pdf' (server local path)
                # unless explicitly configured, which is unlikely in this context.
                return jsonify({'success': False, 'error': 'No CV found. Please build your profile or upload a CV first.'}), 400

        cv_content, ats_analysis = pipeline.cv_engine.generate_tailored_cv(job_data, template_type)
        version_id = list(pipeline.cv_engine.cv_versions.keys())[-1]
        cv_data = pipeline.cv_engine.get_cv_version(version_id) or {}

        from utils.pdf_generator import PDFGenerator
        generator = PDFGenerator()
        header = pipeline.cv_engine._extract_header_info()
        sections = pipeline.cv_engine._build_sections(cv_data)
        cv_html = generator.generate_html(cv_content, template_name=template_type, header=header, sections=sections)

        cl_markdown = pipeline.cv_engine._generate_cover_letter_markdown(job_data, tailored_cv=cv_content)
        header_with_date = dict(header)
        header_with_date['date'] = datetime.now().strftime('%B %d, %Y')
        cl_html = generator.generate_html(cl_markdown, template_name='cover_letter', header=header_with_date)

        return jsonify({'success': True, 'cv_html': cv_html, 'cover_letter_html': cl_html, 'ats': {'analysis': ats_analysis, 'score': cv_data.get('ats_score')}})
    except Exception as e:
        print(f"Apply preview error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/cv', methods=['GET'])
@login_required
def debug_cv():
    """Debug endpoint to check CV rehydration state"""
    try:
        debug_log = []
        def log(msg):
            print(f"DEBUG_EP: {msg}")
            debug_log.append(f"{datetime.now().isoformat()} - {msg}")

        user_id = g.user_id
        log(f"Starting debug for user {user_id}")
        
        # 1. Check Profile in DB
        databases = Databases(g.client)
        try:
            profiles = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                queries=[Query.equal('userId', user_id)]
            )
            log(f"DB: Found {profiles['total']} profiles")
            if profiles['total'] > 0:
                doc = profiles['documents'][0]
                log(f"DB: Profile ID: {doc['$id']}")
                log(f"DB: File ID: {doc.get('cv_file_id') or doc.get('fileId')}")
                log(f"DB: CV Filename: {doc.get('cv_filename')}")
                cv_text = doc.get('cv_text')
                log(f"DB: CV Text Length: {len(cv_text) if cv_text else 0}")
                if not cv_text:
                    log("DB: WARNING - cv_text is empty")
            else:
                log("DB: ERROR - No profile found")
                return jsonify({'success': False, 'log': debug_log, 'error': 'No profile found in DB'})
        except Exception as e:
            log(f"DB: Exception checking profile: {str(e)}")
            log(traceback.format_exc())
            return jsonify({'success': False, 'log': debug_log, 'error': f"DB Check Failed: {str(e)}"})

        # 2. Check Storage logic (Dry run)
        log(f"Storage: UPLOAD_FOLDER is {app.config['UPLOAD_FOLDER']}")
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            log(f"Storage: UPLOAD_FOLDER does not exist! Attempting create...")
            try:
                os.makedirs(app.config['UPLOAD_FOLDER'])
                log("Storage: Created UPLOAD_FOLDER")
            except Exception as e:
                log(f"Storage: Failed to create UPLOAD_FOLDER: {e}")
        else:
            log("Storage: UPLOAD_FOLDER exists and is writable (assumed)")

        # 3. Attempt Rehydration
        log("Rehydration: Attempting _rehydrate_pipeline_from_profile...")
        try:
            # We can't easily capture the internal prints of the function, so we rely on the return
            pipeline = _rehydrate_pipeline_from_profile(user_id, g.client)
            if pipeline:
                log(f"Rehydration: SUCCESS. Pipeline created.")
                log(f"Rehydration: CV Path: {getattr(pipeline, 'cv_path', 'N/A')}")
                cv_content = pipeline.load_cv() if hasattr(pipeline, 'load_cv') else "No load_cv"
                log(f"Rehydration: Loaded CV content length: {len(cv_content) if cv_content and isinstance(cv_content, str) else 'Invalid'}")
            else:
                log("Rehydration: FAILED. Function returned None.")
        except Exception as e:
            log(f"Rehydration: Exception during call: {str(e)}")
            log(traceback.format_exc())

        return jsonify({
            'success': True, 
            'log': debug_log,
            'upload_folder': app.config['UPLOAD_FOLDER']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
