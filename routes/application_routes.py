from flask import Blueprint, request, jsonify, g
from routes.auth_routes import login_required
from appwrite.services.databases import Databases
from appwrite.query import Query
from config import Config
import logging

application_bp = Blueprint('application', __name__)
logger = logging.getLogger(__name__)

from services.task_manager import task_manager
from services.recommendation_engine import engine
from agents.browser_automation import BrowserAutomation
from appwrite.services.storage import Storage
import tempfile
import os

@application_bp.route('/active', methods=['GET'])
@login_required
def get_active_applications():
    """Poll for applications currently being processed"""
    try:
        databases = Databases(g.client)
        # Query for status = 'processing' or 'initializing'
        # Appwrite only supports one OR if we use Query.equal('status', ['processing', 'initializing']) 
        # but that matches any in list.
        result = databases.list_documents(
            database_id=Config.DATABASE_ID,
            collection_id=Config.COLLECTION_ID_APPLICATIONS,
            queries=[
                Query.equal('userId', g.user_id),
                Query.equal('status', ['processing', 'initializing']),
                Query.order_desc('$createdAt'),
                Query.limit(50)
            ]
        )
        
        active_apps = []
        for doc in result['documents']:
            active_apps.append({
                'id': doc['$id'],
                'role': doc.get('role', 'Unknown Position'),
                'company': doc.get('company', 'Unknown Company'),
                'status': doc.get('status'),
                'logs': doc.get('logs', ''), # Assuming we store latest log or step here
                'progress': 50 # Mock progress since we don't have granular steps yet
            })
            
        return jsonify({'success': True, 'active_applications': active_apps})
    except Exception as e:
        logger.error(f"Error fetching active applications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@application_bp.route('/auto-apply', methods=['POST'])
@login_required
def auto_apply():
    try:
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        cv_id = data.get('cv_id')
        
        if not job_ids or not cv_id:
            return jsonify({'success': False, 'error': 'job_ids and cv_id required'}), 400
            
        # Launch background tasks
        for job_id in job_ids:
            task_manager.submit_task(
                _run_auto_apply, 
                args=(job_id, cv_id, g.user_id, g.client)
            )
            
        return jsonify({'success': True, 'message': f'Queued {len(job_ids)} applications'})
    except Exception as e:
        logger.error(f"Error queuing auto-apply: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _run_auto_apply(job_id, cv_id, user_id, client):
    """Background task for auto-application"""
    try:
        # 1. Get Job Details
        job = engine.vector_store.job_map.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in vector store")
            return
            
        job_url = job.get('url') or job.get('job_url')
        if not job_url:
            logger.error(f"Job {job_id} has no URL")
            return
            
        # 2. Download CV to temp file
        storage = Storage(client)
        # Assuming bucket 'cvs' or similar. 
        # TODO: Make bucket configurable or pass it in. 
        # For now, try Config.BUCKET_ID_CVS if exists, else 'application_files'
        bucket_id = getattr(Config, 'BUCKET_ID_CVS', 'application_files')
        
        try:
            file_bytes = storage.get_file_download(bucket_id, cv_id)
        except Exception as e:
            logger.error(f"Failed to download CV {cv_id}: {e}")
            return

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(file_bytes)
            cv_path = tmp.name
            
        # 3. Create Application Record (Pending)
        # Using databases directly as we might not have app context here if threaded?
        # Actually task_manager runs in thread, so we should re-init client if needed or use passed client.
        # But 'client' passed from Flask context might not be thread-safe or valid if request ended.
        # Safer to create new client in thread.
        
        _client = Client()
        _client.set_endpoint(Config.APPWRITE_ENDPOINT)
        _client.set_project(Config.APPWRITE_PROJECT_ID)
        _client.set_key(Config.APPWRITE_API_KEY)
        _db = Databases(_client)
        
        # Create App Record
        from services.job_store import save_application
        # We can't use save_application easily because it expects local files for upload.
        # We'll just create the document directly.
        
        app_data = {
            'company': job.get('company', 'Unknown'),
            'role': job.get('title', 'Unknown'),
            'job_url': job_url,
            'location': job.get('location', ''),
            'status': 'processing',
            'userId': user_id,
            'cv_file_id': cv_id # Store reference
        }
        
        # Check if already exists? Skip for now.
        
        from appwrite.id import ID
        app_doc = _db.create_document(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_APPLICATIONS,
            ID.unique(),
            data=app_data
        )
        app_id = app_doc['$id']

        # 4. Run Browser Automation
        result = {'success': False}
        with BrowserAutomation() as bot:
            # Mock form data for now - in real world, we'd extract from Profile
            # TODO: Fetch Profile from Appwrite
            form_data = {
                'first_name': 'Candidate', # Placeholder
                'last_name': 'User',
                'email': 'user@example.com',
                'phone': '0123456789'
            }
            
            result = bot.apply_to_job(
                job_url, 
                form_data, 
                {'resume': cv_path},
                log_callback=lambda msg: logger.info(f"[{job_id}] {msg}")
            )
            
        # 5. Update Status
        status = 'applied' if result.get('success') else 'failed'
        _db.update_document(
            Config.DATABASE_ID, 
            Config.COLLECTION_ID_APPLICATIONS, 
            app_id, 
            data={'status': status, 'logs': result.get('status', '')}
        )
        
        # Cleanup
        os.unlink(cv_path)
        
    except Exception as e:
        logger.error(f"Auto-apply failed for {job_id}: {e}")

@application_bp.route('', methods=['GET'])
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
        
        result = databases.list_documents(
            database_id=Config.DATABASE_ID,
            collection_id=Config.COLLECTION_ID_APPLICATIONS,
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
                'appliedDate': doc.get('$createdAt', '').split('T')[0],
                'files': doc.get('files')
            })
        return jsonify({
            'applications': applications, 
            'page': page, 
            'limit': limit, 
            'total': result.get('total', len(applications))
        })
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        return jsonify({'applications': [], 'error': str(e)}), 500

@application_bp.route('/<doc_id>/status', methods=['PUT'])
@login_required
def update_application_status(doc_id):
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        allowed = {'pending', 'applied', 'interview', 'rejected'}
        if new_status not in allowed:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
            
        databases = Databases(g.client)
        doc = databases.get_document(Config.DATABASE_ID, Config.COLLECTION_ID_APPLICATIONS, doc_id)
        if doc.get('userId') != g.user_id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
            
        databases.update_document(Config.DATABASE_ID, Config.COLLECTION_ID_APPLICATIONS, doc_id, data={'status': new_status})
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
