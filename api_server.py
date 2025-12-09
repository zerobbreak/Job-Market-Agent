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
import time

# load_dotenv() already called at top


app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "running", 
        "message": "Job Market Agent API is active. If you are looking for the frontend, please ensure you are using the Docker Runtime or a separate frontend host."
    })

# Configure CORS for production
allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,https://job-market-agent.vercel.app,https://job-market-agent.onrender.com').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
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
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

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
        existing_profiles = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', session_id)]
        )
        if existing_profiles.get('total', 0) == 0:
            return None
        doc = existing_profiles['documents'][0]
        file_id = doc.get('cv_file_id') or doc.get('fileId')
        cv_text = doc.get('cv_text')
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
            return pipeline
        if file_id:
            try:
                tmp_name = f"rehydrated_{file_id}.pdf"
                cv_path = os.path.join(app.config['UPLOAD_FOLDER'], tmp_name)
                with open(cv_path, 'wb') as f:
                    data = storage.get_file_download(bucket_id=BUCKET_ID_CVS, file_id=file_id)
                    f.write(data)
                pipeline = JobApplicationPipeline(cv_path=cv_path)
                cv_content = pipeline.load_cv()
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
                return pipeline
            except Exception as e:
                print(f"Rehydrate from storage failed: {e}")
        return None
    except Exception as e:
        print(f"Rehydrate pipeline error: {e}")
        return None



def ensure_profile_schema():
    try:
        api_key = os.getenv('APPWRITE_API_KEY')
        if not api_key:
            return
        admin_client = Client()
        admin_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
        admin_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        admin_client.set_key(api_key)
        admin_db = Databases(admin_client)
        try:
            # Reverted to create_boolean_attribute due to SDK version mismatch (AttributeError)
            # despite deprecation warning.
            admin_db.create_boolean_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                key='notification_enabled',
                required=False,
                default=False
            )
        except Exception as e:
            print(f"Profiles boolean attribute exists or failed to create: {e}")
        try:
            # Reverted to create_integer_attribute due to SDK version mismatch
            admin_db.create_integer_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                key='notification_threshold',
                required=False,
                min=0,
                max=100,
                default=70
            )
        except Exception as e:
            print(f"Profiles integer attribute exists or failed to create: {e}")
    except Exception as e:
        print(f"ensure_profile_schema error: {e}")

ensure_profile_schema()

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
                    cv_content = pipeline.load_cv()
                    pipeline.build_profile(cv_content)
        app_result = pipeline.generate_application_package(job_data, template_type)
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
                    'skills': json.dumps(profile_data.get('skills', [])), # Store as JSON string
                    'experience_level': profile_data.get('experience_level', 'N/A'),
                    'cv_file_id': file_id,
                    'cv_filename': filename,
                    'cv_text': cv_content
                    # Add other fields as needed by your schema
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
                else:
                    # Create new profile
                    databases.create_document(
                        database_id=DATABASE_ID,
                        collection_id=COLLECTION_ID_PROFILES,
                        document_id=ID.unique(),
                        data=profile_doc_data
                    )
                
                # Store pipeline in memory for immediate subsequent requests (like matching)
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
                    Query.order_desc('$createdAt'),
                    Query.limit(1)
                ]
            )
            if cached.get('total', 0) > 0 and not use_demo:
                doc = cached['documents'][0]
                created = doc.get('$createdAt')
                if created:
                    from datetime import datetime, timezone
                    try:
                        ts = datetime.fromisoformat(created.replace('Z', '+00:00')).timestamp()
                        if time.time() - ts < 900:
                            matches = json.loads(doc.get('matches', '[]'))
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
                
                if existing_profiles['total'] > 0:
                    doc = existing_profiles['documents'][0]
                    profile_data = {
                        'skills': json.loads(doc.get('skills', '[]')),
                        'experience_level': doc.get('experience_level', ''),
                        # Reconstruct other fields if saved
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
                # Rehydrate might take time, maybe keep lock or release?
                # Rehydration does IO. Releasing lock then re-acquiring for write is better but race condition possible.
                # Since we are using user-specific keys, race condition is only per user.
                # For simplicity, we'll keep lock or just move hydration out.
                # But pipeline_store is the shared resource.
                pass
        
        if not pipeline:
            pipeline = _rehydrate_pipeline_from_profile(session_id, g.client) or JobApplicationPipeline()
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
        return jsonify({'success': False, 'error': str(e)})

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
                Query.order_desc('$updatedAt'),
                Query.limit(1)
            ]
        )
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
        doc = result['documents'][0]
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
                Query.limit(1)
            ]
        )
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
        doc = result['documents'][0]
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
            Query.order_desc('$createdAt'),
            Query.limit(1)
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
        doc = result['documents'][0]
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
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_profile(profile_text):
    """Parse AI-generated profile text into structured data"""
    profile_data = {
        'skills': [],
        'experience_level': '',
        'education': '',
        'strengths': [],
        'career_goals': ''
    }
    
    try:
        # Try to find JSON content
        json_str = profile_text
        
        # Handle markdown code blocks
        if '```json' in profile_text:
            json_str = profile_text.split('```json')[1].split('```')[0]
        elif '```' in profile_text:
            json_str = profile_text.split('```')[1].split('```')[0]
            
        # Clean up string
        json_str = json_str.strip()
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Update profile data with parsed values
        profile_data.update(data)
        
        # Ensure lists are actually lists
        if isinstance(profile_data['skills'], str):
            profile_data['skills'] = [s.strip() for s in profile_data['skills'].split(',')]
            
        if isinstance(profile_data['strengths'], str):
            profile_data['strengths'] = [s.strip() for s in profile_data['strengths'].split(',')]
            
    except Exception as e:
        print(f"Error parsing profile JSON: {e}")
        # Fallback to regex if JSON parsing fails
        try:
            # Extract skills
            skills_match = re.search(r'(?:Skills|Technical Skills|Expertise)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\n[A-Z]|$)', profile_text, re.IGNORECASE)
            if skills_match:
                skills_text = skills_match.group(1)
                skills = re.findall(r'(?:[-•*]\s*)?([A-Za-z][A-Za-z0-9+#\.\s]+?)(?=[,;\n]|$)', skills_text)
                profile_data['skills'] = [s.strip() for s in skills if len(s.strip()) > 2][:10]
            
            # Extract experience level
            exp_match = re.search(r'(?:Experience Level|Experience|Years)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if exp_match:
                profile_data['experience_level'] = exp_match.group(1).strip()
            
            # Extract education
            edu_match = re.search(r'(?:Education|Degree|Qualification)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if edu_match:
                profile_data['education'] = edu_match.group(1).strip()
            
            # Extract strengths
            strengths_match = re.search(r'(?:Strengths|Key Strengths)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\n[A-Z]|$)', profile_text, re.IGNORECASE)
            if strengths_match:
                strengths_text = strengths_match.group(1)
                strengths = re.findall(r'(?:[-•*]\s*)?([^\n,;]+)', strengths_text)
                profile_data['strengths'] = [s.strip() for s in strengths if len(s.strip()) > 5][:5]
            
            # Extract career goals
            goals_match = re.search(r'(?:Career Goals|Goals|Aspirations)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if goals_match:
                profile_data['career_goals'] = goals_match.group(1).strip()
        except Exception as e2:
            print(f"Error in fallback parsing: {e2}")
    
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
                cv_content = pipeline.load_cv()
                pipeline.build_profile(cv_content)

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
