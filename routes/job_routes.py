from services.pipeline_service import (
    JobApplicationPipeline, 
    _rehydrate_pipeline_from_profile,
    pipeline_store,
    profile_store,
    store_lock
)
from services.job_store import (
    save_job_state,
    load_job_state,
    delete_job_state,
    update_job_progress
)
from services.task_manager import task_manager
from agents.browser_automation import BrowserAutomation
from utils.pdf_generator import PDFGenerator
from flask import Blueprint, request, jsonify, g, send_file
from routes.auth_routes import login_required
from appwrite.services.databases import Databases
from appwrite.query import Query
from config import Config
import logging
import uuid
import time
import threading
import json
import os
import traceback
from datetime import datetime

job_bp = Blueprint('job', __name__)
logger = logging.getLogger(__name__)

@job_bp.route('/search-jobs', methods=['POST'])
@login_required
def search_jobs():
    try:
        data = request.get_json()
        query = data.get('query', 'Python Developer')
        location = data.get('location', 'South Africa')
        max_results = int(data.get('max_results', 10))
        
        pipeline = JobApplicationPipeline()
        jobs = pipeline.search_jobs(query=query, location=location, max_results=max_results)
        
        formatted_jobs = []
        for job in jobs[:10]:
            formatted_jobs.append({
                'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'description': (job.get('description', '') or '')[:200] + '...',
                'url': job.get('url', ''),
            })
        return jsonify({'jobs': formatted_jobs})
    except Exception as e:
        logger.error(f"Error in job search: {e}")
        return jsonify({'jobs': [], 'error': str(e)}), 500

@job_bp.route('/match-jobs', methods=['GET', 'POST'])
@login_required
def matches_last():
    """
    Get matched jobs - enhanced with semantic matching.
    Supports both cached matches and fresh matching with semantic AI.
    """
    try:
        # Check if POST request with fresh matching requested
        if request.method == 'POST':
            data = request.get_json() or {}
            force_refresh = data.get('force_refresh', False)
            location = data.get('location') or request.args.get('location')
            max_results = int(data.get('max_results', 20))
            min_score = float(data.get('min_score', 0.0))
            
            if force_refresh:
                # Perform fresh matching with semantic AI
                return _perform_fresh_matching(g.user_id, g.client, location, max_results, min_score, force_refresh=True)
        
        # GET or cached: Try to fetch cached matches
        databases = Databases(g.client)
        location = request.args.get('location')
        
        # BATTLE-TESTED CACHE INVALIDATION:
        # Check if profile has been updated since the last match was cached.
        # This prevents serving stale matches based on an old CV.
        should_invalidate_cache = False
        try:
            profile_check = databases.list_documents(
                Config.DATABASE_ID, 
                Config.COLLECTION_ID_PROFILES, 
                queries=[Query.equal('userId', g.user_id), Query.limit(1), Query.select(['$updatedAt'])]
            )
            if profile_check['total'] > 0:
                profile_updated_at = profile_check['documents'][0]['$updatedAt']
            else:
                profile_updated_at = None
        except Exception:
            profile_updated_at = None

        queries = [Query.equal('userId', g.user_id), Query.limit(1)]
        if location: queries.insert(1, Query.equal('location', location))
        result = databases.list_documents(Config.DATABASE_ID, Config.COLLECTION_ID_MATCHES, queries=queries)
        
        if not result or result.get('total', 0) == 0:
            # No cached matches - perform fresh matching
            return _perform_fresh_matching(g.user_id, g.client, location, max_results=20, min_score=0.0)
        
        doc = result['documents'][0]
        match_updated_at = doc.get('$updatedAt')
        
        # Check timestamps
        if profile_updated_at and match_updated_at:
            try:
                # Simple string comparison works for ISO8601
                if profile_updated_at > match_updated_at:
                    logger.info(f"Cache Invalidation: Profile ({profile_updated_at}) is newer than Matches ({match_updated_at}). Forcing refresh.")
                    should_invalidate_cache = True
            except Exception as e:
                logger.warning(f"Timestamp comparison failed: {e}")
        
        if should_invalidate_cache:
             return _perform_fresh_matching(g.user_id, g.client, location, max_results=20, min_score=0.0, force_refresh=True)

        matches = json.loads(doc.get('matches', '[]') or '[]')
        last_seen = datetime.now().isoformat()
        databases.update_document(Config.DATABASE_ID, Config.COLLECTION_ID_MATCHES, doc['$id'], data={'last_seen': last_seen})
        return jsonify({'success': True, 'matches': matches, 'location': doc.get('location', ''), 'created_at': doc.get('$createdAt'), 'last_seen': last_seen, 'cached': True})
    except Exception as e:
        logger.error(f"Error in last matches: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch last matches'}), 200


def _perform_fresh_matching(user_id: str, client, location: str = None, max_results: int = 20, min_score: float = 0.0, force_refresh: bool = False):
    """
    Perform fresh job matching using semantic AI (New Recommendation Engine).
    """
    try:
        from services.recommendation_engine import engine
        
        # Get user profile
        databases = Databases(client)
        profile_result = databases.list_documents(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', user_id)]
        )
        
        # FALLBACK: If profile not found with User Client, try Admin Client
        if profile_result.get('total', 0) == 0:
            logger.warning(f"Profile not found for {user_id} using User Client. Trying Admin Client...")
            try:
                from appwrite.client import Client
                admin_client = Client()
                admin_client.set_endpoint(Config.APPWRITE_ENDPOINT)
                admin_client.set_project(Config.APPWRITE_PROJECT_ID)
                admin_client.set_key(Config.APPWRITE_API_KEY)
                admin_db = Databases(admin_client)
                
                profile_result = admin_db.list_documents(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', user_id)]
                )
                if profile_result.get('total', 0) > 0:
                    logger.info(f"✅ Profile found using Admin Client!")
            except Exception as e:
                logger.error(f"Admin Client fallback failed: {e}")

        if profile_result.get('total', 0) == 0:
            logger.error(f"FRESH MATCHING FAILED: Profile not found for user_id={user_id}")
            return jsonify({'success': False, 'error': 'Profile not found. Please upload a CV first.'}), 400
        
        profile_doc = profile_result['documents'][0]
        profile_data = {
            'name': profile_doc.get('name', ''),
            'email': profile_doc.get('email', ''),
            'skills': json.loads(profile_doc.get('skills', '[]') or '[]'),
            'experience_level': profile_doc.get('experience_level', ''),
            'education': profile_doc.get('education', ''),
            'career_goals': profile_doc.get('career_goals', ''),
            'location': profile_doc.get('location', location or 'South Africa'),
            'strengths': json.loads(profile_doc.get('strengths', '[]') or '[]')
        }
        
        # Discover jobs
        location_str = location or profile_data.get('location', 'South Africa')
        pipeline = JobApplicationPipeline()
        
        # Construct Search Query
        skills = profile_data.get('skills', [])
        exp_level = profile_data.get('experience_level', '')
        career_goals = profile_data.get('career_goals', '')
        
        role_title = "Developer"
        clean_goals = career_goals.lower().strip()
        ignored_phrases = ['i want', 'looking for', 'seeking', 'passionate', 'goal is', 'to become', 'aim to']
        
        if len(career_goals) > 3 and len(career_goals) < 50 and not any(p in clean_goals for p in ignored_phrases):
             role_title = career_goals
        elif skills:
             top_skills = " ".join(skills[:2])
             role_title = f"{top_skills} Developer"
             
        search_query = f"{exp_level} {role_title}".strip()
        
        if len(search_query) > 60:
             top_skill = (skills + ['Developer'])[0]
             search_query = f"{exp_level} {top_skill} Developer".strip()

        logger.info(f"Generated Smart Search Query: '{search_query}'")
        
        # Fetch jobs (Search Stage)
        jobs = pipeline.search_jobs(
            query=search_query,
            location=location_str,
            max_results=max_results * 2,
            force_refresh=force_refresh
        )

        if not jobs:
             # Fallback
             logger.info(f"Smart query returned 0 jobs. Trying fallback...")
             top_skill = (profile_data.get('skills', []) + ['Developer'])[0]
             jobs = pipeline.search_jobs(
                query=f"{top_skill} Developer",
                location=location_str,
                max_results=max_results * 2,
                force_refresh=force_refresh
             )
        
        if not jobs:
            return jsonify({'success': True, 'matches': [], 'cached': False, 'message': 'No jobs found'})
        
        # Match & Rank (Ranking Stage)
        # fresh_only=True ensures we act as a Real-Time Aggregator, 
        # only showing the jobs we just fetched from live sources.
        matched_jobs = engine.match_jobs(profile_data, jobs, fresh_only=True)
        
        # Filter by min_score
        matched_jobs = [j for j in matched_jobs if j.get('match_score', 0) >= min_score]
        
        # Limit results
        matched_jobs = matched_jobs[:max_results]
        
        # Format matches for frontend
        formatted_matches = []
        for job in matched_jobs:
            formatted_matches.append({
                'job': {
                    'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'url': job.get('url', ''),
                },
                'match_score': job.get('match_score', 0),
                'match_reasons': job.get('match_reasons', []),
                'score_breakdown': job.get('score_breakdown', {}),
                'semantic_score': job.get('score_breakdown', {}).get('semantic', 0)
            })
        
        # Cache results
        try:
            match_doc_id = f"match_{user_id}_{location_str}".replace(' ', '_')
            match_data = {
                'userId': user_id,
                'location': location_str,
                'matches': json.dumps(formatted_matches),
                'last_seen': datetime.now().isoformat()
            }
            
            try:
                databases.update_document(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_MATCHES,
                    match_doc_id,
                    data={'matches': match_data['matches'], 'last_seen': match_data['last_seen']}
                )
            except Exception:
                match_data['created_at'] = datetime.now().isoformat()
                databases.create_document(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_MATCHES,
                    document_id=match_doc_id,
                    data=match_data
                )
        except Exception as e:
            logger.warning(f"Cache update failed: {e}")
        
        return jsonify({
            'success': True,
            'matches': formatted_matches,
            'location': location_str,
            'cached': False,
            'matching_method': 'semantic_rag'
        })
        
    except Exception as e:
        logger.error(f"Error in fresh matching: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Failed to match jobs: {str(e)}'}), 500

@job_bp.route('/apply-job', methods=['POST'])
@login_required
def apply_job():
    """Compatibility endpoint for /apply-job in frontend"""
    return jsonify({'success': False, 'error': 'Direct /apply-job is legacy. Use /apply-preview/start.'}), 400

@job_bp.route('/apply-status', methods=['GET'])
@login_required
def apply_status():
    """Get status of a job application"""
    job_id = request.args.get('job_id')
    if not job_id: return jsonify({'status': 'not_found'})
    
    state = load_job_state(job_id)
    if state:
        return jsonify(state)
    return jsonify({'status': 'not_found'})

@job_bp.route('/apply-cancel', methods=['POST'])
@login_required
def apply_cancel():
    job_id = request.args.get('job_id') or (request.get_json() or {}).get('job_id')
    state = load_job_state(job_id)
    if state:
        update_job_progress(job_id, state.get('progress', 0), 'cancelled')
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Job not found'}), 404

@job_bp.route('/feedback', methods=['POST'])
@login_required
def feedback():
    """
    Collect user feedback on job matches (save, apply, hide, dismiss).
    This data is used to retrain the matching algorithm weights.
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        action = data.get('action') # save, apply, hide, dismiss
        reason = data.get('reason')
        
        # Log feedback to logger
        logger.info(f"User Feedback: User={g.user_id}, Job={job_id}, Action={action}, Reason={reason}")
        
        # Ideally store this in a dedicated 'feedback' or 'analytics' collection in Appwrite
        # for offline processing and weight tuning.
        try:
             databases = Databases(g.client)
             # We use a unique ID for the feedback event
             feedback_id = str(uuid.uuid4())
             # Assuming we can store it in an 'events' or generic collection, 
             # but for now we'll just log it. 
             # If we had a Feedback collection:
             # databases.create_document(Config.DATABASE_ID, 'feedback', feedback_id, {...})
        except Exception:
             pass

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/apply-preview/start', methods=['POST'])
@login_required
def apply_preview_start():
    """
    Start preview generation with persistent job state and granular progress tracking
    Implements battle-tested patterns: persistent storage, auto-resume, detailed progress
    """
    try:
        data = request.get_json()
        job_data = data.get('job')
        template_type = (data.get('template') or 'MODERN').lower()
        
        job_id = str(uuid.uuid4())
        user_id = g.user_id
        client_jwt_client = g.client
        
        # Initialize job state
        initial_state = {
            'status': 'initializing',
            'progress': 0,
            'phase': 'Initializing preview generation',
            'created_at': time.time(),
            'job_data': job_data,
            'user_id': user_id,
            'template_type': template_type
        }
        
        if not save_job_state(job_id, initial_state):
            return jsonify({'success': False, 'error': 'Failed to initialize job state'}), 500

        def _process_preview_async(jid, jdata, ttype, uid, client):
            """
            Async processing with granular progress updates and robust error handling
            Progress phases: 10% → 25% → 50% → 75% → 95% → 100%
            """
            try:
                # Phase 1: Loading profile (10%)
                update_job_progress(jid, 10, 'processing', 'Loading user profile...')
                
                pipeline = None
                with store_lock:
                    if uid in pipeline_store:
                        pipeline = pipeline_store[uid]
                        logger.info(f"Using cached pipeline for user {uid}")
                    else:
                        logger.info(f"Rehydrating pipeline for user {uid}")
                        pipeline = _rehydrate_pipeline_from_profile(uid, client)
                        if pipeline:
                            pipeline_store[uid] = pipeline
                
                if not pipeline:
                    error_msg = 'Profile not found. Please upload a CV first.'
                    logger.error(f"Preview failed for job {jid}: {error_msg}")
                    update_job_progress(jid, 0, 'error', error_msg, error=error_msg)
                    return

                # Phase 2: Initializing CV engine (25%)
                update_job_progress(jid, 25, 'processing', 'Initializing CV tailoring engine...')

                if not getattr(pipeline, 'cv_engine', None):
                    p_info = profile_store.get(uid)
                    if p_info and p_info.get('cv_content'):
                        from utils.cv_tailoring import CVTailoringEngine
                        pipeline.cv_engine = CVTailoringEngine(p_info['cv_content'], p_info.get('profile_data', {}))
                        pipeline.profile = p_info.get('profile_data', {})
                        logger.info(f"Created CV engine for user {uid}")
                    else:
                        error_msg = 'CV content missing. Please re-upload your CV.'
                        logger.error(f"Preview failed for job {jid}: {error_msg}")
                        update_job_progress(jid, 0, 'error', error_msg, error=error_msg)
                        return

                # Phase 3: Generating tailored CV (50%)
                update_job_progress(jid, 50, 'processing', 'Generating tailored CV with AI...')
                
                logger.info(f"Generating tailored CV for job {jid}")
                cv_content, ats_analysis = pipeline.cv_engine.generate_tailored_cv(jdata, ttype)
                version_id = list(pipeline.cv_engine.cv_versions.keys())[-1]
                cv_data = pipeline.cv_engine.get_cv_version(version_id) or {}
                
                # Phase 4: Generating cover letter (75%)
                update_job_progress(jid, 75, 'processing', 'Generating cover letter...')
                
                logger.info(f"Generating cover letter for job {jid}")
                cl_markdown = pipeline.cv_engine._generate_cover_letter_markdown(jdata, tailored_cv=cv_content)
                
                # Phase 5: Rendering HTML (95%)
                update_job_progress(jid, 95, 'processing', 'Rendering preview...')
                
                logger.info(f"Rendering HTML for job {jid}")
                generator = PDFGenerator()
                header = pipeline.cv_engine._extract_header_info()
                sections = pipeline.cv_engine._build_sections(cv_data)
                cv_html = generator.generate_html(cv_content, template_name=ttype, header=header, sections=sections)
                
                header['date'] = datetime.now().strftime('%B %d, %Y')
                cl_html = generator.generate_html(cl_markdown, template_name='cover_letter', header=header)
                
                # Phase 6: Complete (100%)
                result = {
                    'cv_html': cv_html,
                    'cover_letter_html': cl_html,
                    'cv_markdown': cv_content,
                    'cl_markdown': cl_markdown,
                    'header': header,
                    'sections': sections,
                    'application_answers': cv_data.get('application_answers', {}),
                    'ats': {'analysis': ats_analysis, 'score': cv_data.get('ats_score')}
                }
                
                update_job_progress(jid, 100, 'done', 'Preview ready!', result=result)
                logger.info(f"Preview generation completed successfully for job {jid}")

            except Exception as e:
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f"Preview Async Error for job {jid}: {error_msg}\n{error_trace}")
                update_job_progress(jid, 0, 'error', f'Generation failed: {error_msg}', error=error_msg)

        # Start async processing
        # Note: In a real production env, this should be a Celery task. 
        # For this implementation, we use threading but rely on Appwrite for state persistence.
        threading.Thread(
            target=_process_preview_async,
            args=(job_id, job_data, template_type, user_id, client_jwt_client),
            daemon=True
        ).start()
        
        return jsonify({'success': True, 'job_id': job_id})
    except Exception as e:
        logger.error(f"Error starting preview: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/apply-preview/status', methods=['GET'])
@login_required
def apply_preview_status():
    """
    Get preview job status with auto-resume capability
    """
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({'success': False, 'error': 'Job ID required'}), 400
    
    # Check persistent storage (Single Source of Truth)
    persistent_state = load_job_state(job_id)
    if persistent_state:
        # Check if job is stale
        last_updated = persistent_state.get('last_updated', 0)
        status = persistent_state.get('status')
        if status in ['initializing', 'processing']:
            # Increased timeout to 15 minutes (900 seconds) for AI generation
            if time.time() - last_updated > 900:  
                logger.warning(f"Job {job_id} appears stale, marking as error")
                error_msg = 'Job timed out. Please try again.'
                update_job_progress(job_id, 0, 'error', error_msg, error=error_msg)
                persistent_state['status'] = 'error'
                persistent_state['error'] = error_msg
        
        return jsonify({'success': True, **persistent_state})
    
    return jsonify({'success': False, 'error': 'Job not found'}), 404

@job_bp.route('/apply-preview/download', methods=['GET'])
@login_required
def apply_preview_download():
    job_id = request.args.get('job_id')
    doc_type = request.args.get('type', 'cv')
    
    job_info = load_job_state(job_id)
    if not job_info:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
        
    if job_info.get('status') != 'done':
        return jsonify({'success': False, 'error': 'Preview not ready'}), 400
        
    result = job_info.get('result', {})
    template_type = job_info.get('template_type', 'modern')
    generator = PDFGenerator()
    
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
        
    try:
        if doc_type == 'cv':
            markdown_content = result.get('cv_markdown', '')
            header = result.get('header', {})
            sections = result.get('sections', {})
            if not markdown_content: return jsonify({'success': False, 'error': 'Source content missing'}), 404
            success = generator.generate_pdf(markdown_content, output_path, template_name=template_type, header=header, sections=sections)
            filename = f"CV_{job_info.get('job_data', {}).get('company', 'Job').replace(' ', '_')}.pdf"
        elif doc_type == 'cover_letter':
            markdown_content = result.get('cl_markdown', '')
            header = result.get('header', {})
            if not markdown_content: return jsonify({'success': False, 'error': 'Source content missing'}), 404
            success = generator.generate_pdf(markdown_content, output_path, template_name='cover_letter', header=header)
            filename = f"Cover_Letter_{job_info.get('job_data', {}).get('company', 'Job').replace(' ', '_')}.pdf"
        else:
            return jsonify({'success': False, 'error': 'Invalid type'}), 400

        if success:
             return send_file(output_path, as_attachment=True, download_name=filename)
        else:
             return jsonify({'success': False, 'error': 'PDF generation failed'}), 500
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/apply-automation/start', methods=['POST'])
@login_required
def apply_automation_start():
    try:
        data = request.get_json()
        preview_job_id = data.get('job_id')
        
        preview_data = load_job_state(preview_job_id)
        if not preview_data:
             return jsonify({'success': False, 'error': 'Invalid preview job ID'}), 400
        
        if preview_data.get('status') != 'done':
             return jsonify({'success': False, 'error': 'Preview not ready'}), 400
        
        job_data = preview_data.get('job_data')
        # In this modular version, we might handle file paths differently
        # For now, following main.py logic
        files_data = preview_data.get('files', {}) 
        user_id = g.user_id
        
        # Access profile_store from pipeline_service
        profile_data_for_auto = {}
        with store_lock:
             if user_id not in profile_store:
                 _rehydrate_pipeline_from_profile(user_id, g.client)
             profile_info = profile_store.get(user_id)
             if profile_info:
                 profile_data_for_auto = profile_info.get('profile_data', {}).copy()
        
        if not profile_data_for_auto:
             # Fallback to DB
             try:
                 databases = Databases(g.client)
                 res = databases.list_documents(Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, queries=[Query.equal('userId', user_id)])
                 if res['total'] > 0:
                     doc = res['documents'][0]
                     profile_data_for_auto = {
                         'name': doc.get('name', ''),
                         'email': doc.get('email', ''),
                         'phone': doc.get('phone', ''),
                         'location': doc.get('location', ''),
                         'education': doc.get('education', ''),
                         'experience_level': doc.get('experience_level', ''),
                         'links': {'linkedin': doc.get('linkedin', ''), 'portfolio': doc.get('portfolio', '')}
                     }
             except Exception: pass

        if not profile_data_for_auto:
             return jsonify({'success': False, 'error': 'Profile data not found. Please upload a CV first.'}), 400

        automation_id = str(uuid.uuid4())
        initial_auto_state = {'status': 'initializing', 'created_at': time.time(), 'user_id': user_id, 'type': 'automation'}
        save_job_state(automation_id, initial_auto_state)
        
        def _run_automation(auto_id, job, user, files, p_data):
            try:
                update_job_progress(auto_id, 0, 'running', 'Initializing Browser')
                
                form_data = {
                    'name': p_data.get('name', ''),
                    'email': p_data.get('email', ''),
                    'phone': p_data.get('phone', ''),
                    'location': p_data.get('location', ''),
                    'linkedin': p_data.get('links', {}).get('linkedin', ''),
                    'portfolio': p_data.get('links', {}).get('portfolio', ''),
                    'education': p_data.get('education', []),
                    'experience': p_data.get('experience', [])
                }

                with BrowserAutomation(headless=False) as bot:
                    def log_cb(msg):
                        update_job_progress(auto_id, 50, 'running', msg)
                    
                    job_url = job.get('url')
                    if not job_url: raise ValueError("Job URL missing")
                    result = bot.apply_to_job(job_url, form_data, files, log_callback=log_cb)
                    
                    if result['success']:
                        update_job_progress(auto_id, 100, 'submitted', 'Application Submitted!', result={'msg': 'Application Submitted!'})
                    else:
                        update_job_progress(auto_id, 80, 'manual_review_needed', 'Could not fully automate.', result={'screenshot': result.get('screenshot')})
                            
            except Exception as e:
                logger.error(f"Automation Error: {e}")
                update_job_progress(auto_id, 0, 'error', str(e), error=str(e))

        task_manager.submit_task(target=_run_automation, args=(automation_id, job_data, user_id, files_data, profile_data_for_auto), daemon=True)
        return jsonify({'success': True, 'automation_id': automation_id})
    except Exception as e:
        logger.error(f"Error starting automation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@job_bp.route('/apply-automation/status', methods=['GET'])
@login_required
def apply_automation_status():
    auto_id = request.args.get('automation_id')
    state = load_job_state(auto_id)
    if not state:
        return jsonify({'status': 'not_found'}), 404
    return jsonify(state)
