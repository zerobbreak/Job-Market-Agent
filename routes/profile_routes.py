from flask import Blueprint, request, jsonify, g, send_file, Response  # type: ignore
from routes.auth_routes import login_required
from services.pipeline_service import (
    JobApplicationPipeline, 
    _rehydrate_pipeline_from_profile,
    parse_profile,
    pipeline_store,
    profile_store,
    store_lock
)
from services.cv_analysis_service import generate_ai_analysis
from appwrite.services.tables_db import TablesDB  # type: ignore
from appwrite.services.storage import Storage  # type: ignore
from appwrite.query import Query  # type: ignore
from appwrite.id import ID  # type: ignore
from config import Config
from werkzeug.utils import secure_filename  # type: ignore
import json
import logging
import os
import hashlib
import re
from datetime import datetime
from io import BytesIO
import requests as _req

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

@profile_bp.route('/current', methods=['GET'])
@login_required
def get_current_profile():
    try:
        tablesDB = TablesDB(g.client)
        # 1. Try to find explicitly active profile
        result = tablesDB.list_rows(
            Config.DATABASE_ID, 
            Config.COLLECTION_ID_PROFILES, 
            queries=[
                Query.equal('userId', g.user_id), 
                Query.equal('is_active', True),
                Query.limit(1)
            ]
        )
        
        # 2. Fallback to most recently updated if no active profile found
        if result.get('total', 0) == 0:
            result = tablesDB.list_rows(
                Config.DATABASE_ID, 
                Config.COLLECTION_ID_PROFILES, 
                queries=[
                    Query.equal('userId', g.user_id), 
                    Query.order_desc('$updatedAt'),
                    Query.limit(1)
                ]
            )
            
        if result.get('total', 0) == 0:
            # Return empty profile instead of 404
            return jsonify({
                'success': True,
                'cv_filename': None,
                'uploaded_at': None,
                'is_active': False,
                'message': 'No profile found. Please upload a CV to get started.'
            })
        
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        if not rows:
            return jsonify({
                'success': True,
                'cv_filename': None,
                'uploaded_at': None,
                'is_active': False,
                'message': 'No profile found. Please upload a CV to get started.'
            })
        doc = rows[0]
        return jsonify({
            'success': True, 
            'cv_filename': doc.get('cv_filename', 'Unknown'), 
            'uploaded_at': doc.get('$updatedAt', doc.get('$createdAt')),
            'is_active': doc.get('is_active', False)
        })
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/structured', methods=['GET'])
@login_required
def get_structured_profile():
    try:
        tablesDB = TablesDB(g.client)
        result = tablesDB.list_rows(Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, queries=[Query.equal('userId', g.user_id), Query.limit(1)])
        
        # Return empty profile instead of 404 when no profile exists
        if result.get('total', 0) == 0:
            return jsonify({
                'success': True,
                'profile': {
                    'name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'skills': [],
                    'experience_level': '',
                    'education': '',
                    'strengths': [],
                    'career_goals': '',
                    'notification_enabled': False,
                    'notification_threshold': 70
                },
                'message': 'No profile found. Please upload a CV to get started.'
            })
        
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        if not rows:
            return jsonify({
                'success': True,
                'profile': {
                    'name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'skills': [],
                    'experience_level': '',
                    'education': '',
                    'strengths': [],
                    'career_goals': '',
                    'notification_enabled': False,
                    'notification_threshold': 70
                },
                'message': 'No profile found. Please upload a CV to get started.'
            })
        doc = rows[0]
        
        def _safe_json(field, default):
            try:
                v = doc.get(field)
                if isinstance(v, str):
                    if not v.strip(): return default
                    return json.loads(v)
                return v if v is not None else default
            except Exception: return default
            
        profile = {
            'name': doc.get('name', '') or '',
            'email': doc.get('email', '') or '',
            'phone': doc.get('phone', '') or '',
            'location': doc.get('location', '') or '',
            'skills': _safe_json('skills', []),
            'experience_level': doc.get('experience_level', '') or '',
            'education': doc.get('education', '') or '',
            'strengths': _safe_json('strengths', []),
            'career_goals': doc.get('career_goals', '') or '',
            'notification_enabled': bool(doc.get('notification_enabled', False)),
            'notification_threshold': int(doc.get('notification_threshold', 70) or 70)
        }
        
        if not profile['name'] or not profile['email'] or not profile['skills']:
            pipeline = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            if pipeline and pipeline.profile:
                healed_data = parse_profile(pipeline.profile)
                profile.update({k: v for k, v in healed_data.items() if not profile.get(k)})
                try:
                    tablesDB.update_row(Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, doc['$id'], data={'name': profile['name'], 'email': profile['email']})
                except Exception: pass
                    
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _safe_json(field, default, doc):
    """Parse JSON field from profile document."""
    try:
        v = doc.get(field)
        if isinstance(v, str):
            if not v.strip():
                return default
            return json.loads(v)
        return v if v is not None else default
    except Exception:
        return default


@profile_bp.route('/cv-analysis', methods=['GET'])
@login_required
def get_cv_analysis():
    """
    CV Analysis route for the dashboard CV Analysis tab.
    Returns parsed CV details (uploaded document) and AI-generated analysis:
    match readiness percentage, assessment message, and critical skill gaps.
    """
    try:
        tablesDB = TablesDB(g.client)
        # Fetch active or latest profile
        result = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.equal('is_active', True),
                Query.limit(1),
            ],
        )
        if result.get('total', 0) == 0:
            result = tablesDB.list_rows(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                queries=[
                    Query.equal('userId', g.user_id),
                    Query.order_desc('$updatedAt'),
                    Query.limit(1),
                ],
            )
        if result.get('total', 0) == 0:
            return jsonify({
                'success': False,
                'error': 'No profile found. Please upload a CV to get started.',
                'uploaded_document': None,
                'ai_analysis': None,
            }), 404

        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        if not rows:
            return jsonify({
                'success': False,
                'error': 'No profile found. Please upload a CV to get started.',
                'uploaded_document': None,
                'ai_analysis': None,
            }), 404
        doc = rows[0]

        def _sj(f, d):
            return _safe_json(f, d, doc)

        profile = {
            'name': doc.get('name') or '',
            'email': doc.get('email') or '',
            'phone': doc.get('phone') or '',
            'location': doc.get('location') or '',
            'skills': _sj('skills', []),
            'experience_level': doc.get('experience_level') or '',
            'education': _sj('education', []),
            'strengths': _sj('strengths', []),
            'career_goals': doc.get('career_goals') or '',
            'work_experience': _sj('work_experience', []),
            'links': _sj('links', {}),
        }
        if not profile['name'] or not profile['skills']:
            pipeline = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            if pipeline and pipeline.profile:
                healed = parse_profile(pipeline.profile)
                profile.update({k: v for k, v in healed.items() if (not profile.get(k) and v)})

        # Improve name fallback - try to derive from email or other contact info
        candidate_name = profile.get('name') or ''
        if not candidate_name:
            # Try to extract name from email prefix
            email = profile.get('email') or ''
            if email and '@' in email:
                prefix = email.split('@')[0]
                # Clean the prefix
                prefix = re.sub(r'[._-]', ' ', prefix)
                prefix = re.sub(r'\b\d+\b', ' ', prefix)
                prefix = re.sub(r'\s+', ' ', prefix).strip()
                words = [w for w in prefix.split() if len(w) > 1 and w.isalpha()]
                if words and len(words) <= 5:
                    candidate_name = ' '.join(w.title() for w in words)
            
            # Try to extract from LinkedIn if available
            if not candidate_name:
                links = profile.get('links', {})
                if not isinstance(links, dict):
                    links = {}
                linkedin = links.get('linkedin', '') or links.get('LinkedIn', '')
                if linkedin:
                    username_match = re.search(r'/in/([^/?]+)', linkedin)
                    if username_match:
                        username = username_match.group(1)
                        name_parts = username.replace('-', ' ').replace('_', ' ').split()
                        name_parts = [p for p in name_parts if p.isalpha() and len(p) > 1]
                        if name_parts and len(name_parts) <= 5:
                            candidate_name = ' '.join(p.title() for p in name_parts)
            
            # If still no name, use UNKNOWN
            if not candidate_name:
                candidate_name = 'UNKNOWN'

        cv_filename = doc.get('cv_filename') or 'Unknown'
        uploaded_at = doc.get('$updatedAt') or doc.get('$createdAt')
        exp = profile.get('experience_level') or 'Entry Level'
        work_arrangement = 'Hybrid / Remote'
        role_type = f"{exp} • {work_arrangement}"
        summary = (profile.get('career_goals') or '').strip() or 'Not specified'
        skills = list(profile.get('skills') or [])
        skill_density = min(100, 15 + len(skills) * 4) if skills else 15

        # Build meaningful experience string from work_experience
        work_experience = profile.get('work_experience', [])
        if not isinstance(work_experience, list):
            work_experience = []
        
        if work_experience and len(work_experience) > 0:
            # Get most recent company
            most_recent = work_experience[0] if work_experience else {}
            if isinstance(most_recent, dict):
                company = most_recent.get('company', '') or most_recent.get('company_name', '')
            else:
                company = ''
            
            num_roles = len(work_experience)
            if company:
                experience_str = f"{exp} • {num_roles} role{'s' if num_roles > 1 else ''} at {company}"
            else:
                experience_str = f"{exp} • {num_roles} role{'s' if num_roles > 1 else ''}"
        elif exp:
            experience_str = f"{exp} • No experience listed"
        else:
            experience_str = "Not specified"

        uploaded_document = {
            'candidate_name': candidate_name,
            'role_type': role_type,
            'professional_summary': summary,
            'core_skills': skills,
            'experience': experience_str,
            'skill_density_alignment': skill_density,
            'cv_filename': cv_filename,
            'uploaded_at': uploaded_at,
        }

        matches_sample = []
        try:
            mq = [
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt'),
                Query.limit(1),
            ]
            mres = tablesDB.list_rows(
                Config.DATABASE_ID, Config.COLLECTION_ID_MATCHES, queries=mq
            )
            if mres.get('total', 0) > 0:
                # TablesDB returns 'rows' instead of 'documents' in the new API
                match_rows = mres.get('rows', mres.get('documents', []))
                if match_rows:
                    raw = match_rows[0].get('matches', '[]') or '[]'
                    matches_sample = json.loads(raw) if isinstance(raw, str) else raw
                    if not isinstance(matches_sample, list):
                        matches_sample = []
        except Exception as e:
            logger.debug(f"Could not fetch matches for cv-analysis: {e}")

        ai_analysis = generate_ai_analysis(profile, matches_sample or None)
        parsing_status = {
            'active': True,
            'progress': 100,
            'message': 'Complete',
        }

        return jsonify({
            'success': True,
            'uploaded_document': uploaded_document,
            'ai_analysis': ai_analysis,
            'parsing_status': parsing_status,
        })
    except Exception as e:
        logger.error(f"Error in cv-analysis: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'uploaded_document': None,
            'ai_analysis': None,
        }), 500


@profile_bp.route('/profile', methods=['PUT'], strict_slashes=False)
@login_required
def update_profile():
    """
    Battle-tested profile update endpoint following REST API best practices.
    Implements industry-standard approach used by Stripe, GitHub API, and AWS API Gateway.
    
    Features:
    - Full resource update (PUT semantics)
    - Input validation
    - Atomic database updates
    - In-memory cache synchronization
    - Proper error handling with HTTP status codes
    """
    try:
        # Step 1: Parse and validate request body
        if not request.is_json:
            return jsonify({
                'success': False, 
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'error': 'Request body is required'
            }), 400
        
        # Step 2: Get existing profile document
        tablesDB = TablesDB(g.client)
        result = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', g.user_id), Query.limit(1)]
        )
        
        if result.get('total', 0) == 0:
            return jsonify({
                'success': False, 
                'error': 'No profile found. Please upload a CV first.'
            }), 404
        
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        if not rows:
            return jsonify({
                'success': False, 
                'error': 'No profile found. Please upload a CV first.'
            }), 404
        doc = rows[0]
        doc_id = doc['$id']
        
        # Step 3: Validate and sanitize input data
        # Extract fields with defaults (following defensive programming practices)
        update_data = {}
        
        # String fields - sanitize and validate
        string_fields = ['name', 'email', 'phone', 'location', 'experience_level', 'education', 'career_goals']
        for field in string_fields:
            if field in data:
                value = str(data[field]).strip() if data[field] is not None else ''
                update_data[field] = value
        
        # Array fields - validate JSON serializable
        array_fields = ['skills', 'strengths']
        for field in array_fields:
            if field in data:
                value = data[field]
                if isinstance(value, list):
                    # Ensure all items are strings
                    update_data[field] = json.dumps([str(item).strip() for item in value if item])
                elif isinstance(value, str):
                    # Try to parse if it's a JSON string
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            update_data[field] = json.dumps([str(item).strip() for item in parsed if item])
                        else:
                            update_data[field] = json.dumps([])
                    except json.JSONDecodeError:
                        # If not JSON, treat as comma-separated string
                        items = [s.strip() for s in value.split(',') if s.strip()]
                        update_data[field] = json.dumps(items)
                else:
                    update_data[field] = json.dumps([])
        
        # Boolean fields
        if 'notification_enabled' in data:
            update_data['notification_enabled'] = bool(data['notification_enabled'])
        
        # Integer fields with validation
        if 'notification_threshold' in data:
            threshold = int(data['notification_threshold'])
            # Clamp between 0 and 100
            update_data['notification_threshold'] = max(0, min(100, threshold))
        
        # Step 4: Update database document atomically
        try:
            tablesDB.update_row(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                doc_id,
                data=update_data
            )
            logger.info(f"Updated profile document {doc_id} for user {g.user_id}")
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            return jsonify({
                'success': False, 
                'error': f'Failed to update profile: {str(e)}'
            }), 500
        
        # Step 5: Rehydrate updated profile data for response
        updated_result = tablesDB.get_row(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            doc_id
        )
        
        def _safe_json(field, default):
            try:
                v = updated_result.get(field)
                if isinstance(v, str):
                    if not v.strip():
                        return default
                    return json.loads(v)
                return v if v is not None else default
            except Exception:
                return default
        
        updated_profile = {
            'name': updated_result.get('name', '') or '',
            'email': updated_result.get('email', '') or '',
            'phone': updated_result.get('phone', '') or '',
            'location': updated_result.get('location', '') or '',
            'skills': _safe_json('skills', []),
            'experience_level': updated_result.get('experience_level', '') or '',
            'education': updated_result.get('education', '') or '',
            'strengths': _safe_json('strengths', []),
            'career_goals': updated_result.get('career_goals', '') or '',
            'notification_enabled': bool(updated_result.get('notification_enabled', False)),
            'notification_threshold': int(updated_result.get('notification_threshold', 70) or 70)
        }
        
        # Step 6: Update in-memory stores for consistency
        # This ensures the pipeline service has the latest data
        try:
            with store_lock:
                if g.user_id in profile_store:
                    profile_store[g.user_id]['profile_data'] = updated_profile
                    profile_store[g.user_id]['raw_profile'] = updated_result
                
                # Optionally rehydrate pipeline if it exists
                if g.user_id in pipeline_store:
                    pipeline = pipeline_store[g.user_id]
                    if pipeline and hasattr(pipeline, 'profile'):
                        # Update pipeline's profile data
                        pipeline.profile = updated_profile
        except Exception as e:
            logger.warning(f"Failed to update in-memory stores: {e}")
            # Non-critical - continue with response
        
        # Step 7: Return success response with updated profile
        return jsonify({
            'success': True,
            'profile': updated_profile,
            'message': 'Profile updated successfully'
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error in update_profile: {e}")
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to update profile: {str(e)}'
        }), 500

def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file for deduplication"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _validate_cv_file(cv_file) -> tuple[bool, str]:
    """Validate CV file before processing"""
    if not cv_file:
        return False, "No file provided"
    
    # Check file extension
    filename = cv_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.pdf', '.doc', '.docx']:
        return False, f"Invalid file type. Only PDF, DOC, and DOCX files are allowed."
    
    # Check file size (10MB limit)
    cv_file.seek(0, os.SEEK_END)
    file_size = cv_file.tell()
    cv_file.seek(0)  # Reset to beginning
    
    max_size = Config.MAX_CONTENT_LENGTH
    if file_size > max_size:
        return False, f"File too large. Maximum size is {max_size / (1024*1024):.1f}MB"
    
    if file_size < 1024:  # Less than 1KB is suspicious
        return False, "File appears to be empty or corrupted"
    
    return True, ""

def _set_active_exclusive(tablesDB, user_id, active_profile_id):
    """
    Sets the specified profile as active and ensures all other profiles 
    for the user are set to inactive.
    """
    try:
        # 1. Find currently active profiles for this user
        active_profiles = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', user_id),
                Query.equal('is_active', True)
            ]
        )
        
        # 2. Deactivate them (unless it's the target one)
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = active_profiles.get('rows', active_profiles.get('documents', []))
        for doc in rows:
            if doc['$id'] != active_profile_id:
                tablesDB.update_row(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    doc['$id'],
                    data={'is_active': False}
                )
                logger.info(f"Deactivated profile {doc['$id']}")
        
        # 3. Activate the target profile
        # We do this unconditionally to ensure it's set to True
        tablesDB.update_row(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            active_profile_id,
            data={'is_active': True}
        )
        logger.info(f"Activated profile {active_profile_id}")
                
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        raise e  # Propagate error so the caller knows it failed

@profile_bp.route('/analyze-cv', methods=['POST'])
@login_required
def analyze_cv():
    """
    Battle-tested idempotent CV upload with hash-based deduplication.
    Implements industry-standard approach used by AWS S3, Google Cloud Storage, etc.
    """
    try:
        cv_file = request.files.get('cv')
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'
        
        # Step 1: Validate file
        is_valid, error_msg = _validate_cv_file(cv_file)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Step 2: Save file temporarily to calculate hash
        filename = secure_filename(cv_file.filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        temp_path = os.path.join(Config.UPLOAD_FOLDER, f"temp_{g.user_id}_{filename}")
        cv_file.save(temp_path)
        
        # Step 3: Calculate file hash for deduplication
        file_hash = _calculate_file_hash(temp_path)
        logger.info(f"CV upload: file_hash={file_hash[:16]}... for user={g.user_id}")
        
        # Step 4: Check for existing CV with same hash (idempotent check)
        tablesDB = TablesDB(g.client)
        storage = Storage(g.client)
        
        existing_profiles = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', g.user_id)]
        )
        
        existing_profile = None
        if existing_profiles.get('total', 0) > 0:
            # TablesDB returns 'rows' instead of 'documents' in the new API
            rows = existing_profiles.get('rows', existing_profiles.get('documents', []))
            for doc in rows:
                existing_hash = doc.get('cv_hash')
                if existing_hash == file_hash:
                    existing_profile = doc
                    logger.info(f"Found existing CV with matching hash for user={g.user_id}")
                    break
        
        # Step 5: Handle idempotent upload (same file already exists)
        # CRITICAL FIX: Only restore if overwrite is FALSE. If overwrite is TRUE, skip this and process as new.
        if existing_profile and not overwrite:
            # Rehydrate profile from database instead of re-analyzing
            logger.info(f"Idempotent upload detected - rehydrating profile for user={g.user_id}")
            
            # Try to rehydrate pipeline
            pipeline = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            
            # Get profile data from database
            def _safe_json(field, default):
                try:
                    v = existing_profile.get(field)
                    if isinstance(v, str):
                        if not v.strip(): return default
                        return json.loads(v)
                    return v if v is not None else default
                except Exception: 
                    return default
            
            parsed = {
                'name': existing_profile.get('name', '') or '',
                'email': existing_profile.get('email', '') or '',
                'phone': existing_profile.get('phone', '') or '',
                'location': existing_profile.get('location', '') or '',
                'skills': _safe_json('skills', []),
                'experience_level': existing_profile.get('experience_level', '') or '',
                'education': _safe_json('education', []),
                'work_experience': _safe_json('work_experience', []),
                'projects': _safe_json('projects', []),
                'strengths': _safe_json('strengths', []),
                'career_goals': existing_profile.get('career_goals', '') or '',
            }
            
            # If rehydration succeeded, use that data
            if pipeline and pipeline.profile:
                rehydrated = parse_profile(pipeline.profile)
                parsed.update({k: v for k, v in rehydrated.items() if v})
            
            # Update in-memory stores
            with store_lock:
                if pipeline:
                    pipeline_store[g.user_id] = pipeline
                profile_store[g.user_id] = {
                    'profile_data': parsed,
                    'raw_profile': existing_profile,
                    'cv_filename': existing_profile.get('cv_filename', filename),
                    'cv_content': existing_profile.get('cv_text', '')
                }
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            return jsonify({
                'success': True, 
                'profile': parsed, 
                'cv_filename': existing_profile.get('cv_filename', filename),
                'idempotent': True,
                'message': 'CV already exists. Profile data restored.'
            })
        
        # Step 6: Process new CV upload
        logger.info(f"Processing new CV upload for user={g.user_id}")
        cv_path = os.path.join(Config.UPLOAD_FOLDER, f"{g.user_id}_{filename}")
        
        # Move temp file to final location
        try:
            if os.path.exists(cv_path):
                os.remove(cv_path)
            os.rename(temp_path, cv_path)
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            cv_path = temp_path  # Fallback to temp path
        
        # Step 7: Analyze CV
        pipeline = JobApplicationPipeline(cv_path=cv_path)
        cv_content = pipeline.load_cv()
        profile_data = pipeline.build_profile(cv_content)
        parsed = parse_profile(profile_data)
        
        # Step 8: Persist to Appwrite Storage
        cv_file_id = None
        try:
            # Read file as bytes
            with open(cv_path, 'rb') as f:
                file_bytes = f.read()
            
            # Create a BytesIO object for Appwrite (file-like object)
            file_obj = BytesIO(file_bytes)
            file_obj.name = filename  # Set filename for Appwrite
            file_obj.seek(0)  # Reset to beginning of file
            
            cv_file_id = storage.create_file(
                bucket_id=Config.BUCKET_ID_CVS,
                file_id=ID.unique(),
                file=file_obj,
                permissions=[f"read({g.user_id})"]
            )['$id']
            logger.info(f"CV saved to Appwrite storage: {cv_file_id}")
        except Exception as e:
            logger.warning(f"Failed to save CV to Appwrite storage: {e}")
            # Continue without storage - file is still on disk
        
        # Step 9: Save profile to database
        try:
            profile_data_for_db = {
                'userId': g.user_id,
                'name': parsed.get('name', ''),
                'email': parsed.get('email', ''),
                'phone': parsed.get('phone', ''),
                'location': parsed.get('location', ''),
                'skills': json.dumps(parsed.get('skills', [])),
                'experience_level': parsed.get('experience_level', ''),
                'education': json.dumps(parsed.get('education', [])),
                # 'work_experience' removed as it's not in schema
                # 'projects': json.dumps(parsed.get('projects', [])), # projects also not in schema dump
                'strengths': json.dumps(parsed.get('strengths', [])),
                'career_goals': parsed.get('career_goals', ''),
                'cv_filename': filename,
                'cv_hash': file_hash,
                'cv_file_id': cv_file_id,
                # 'cv_text': cv_content[:50000] if len(cv_content) > 50000 else cv_content  # Limit text size - REMOVED: Not in schema
            }
            
            # Update existing profile or create new one
            final_profile_id = None
            if existing_profile:
                final_profile_id = existing_profile['$id']
                tablesDB.update_row(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    final_profile_id,
                    data=profile_data_for_db
                )
                logger.info(f"Updated existing profile for user={g.user_id}")
            else:
                new_doc = tablesDB.create_row(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    document_id=ID.unique(),
                    data=profile_data_for_db
                )
                final_profile_id = new_doc['$id']
                logger.info(f"Created new profile for user={g.user_id}")
            
            # Set as active
            _set_active_exclusive(tablesDB, g.user_id, final_profile_id)
        except Exception as e:
            logger.error(f"Failed to save profile to database: {e}")
            # Do NOT continue silently. Fail the request so frontend knows.
            return jsonify({'success': False, 'error': f'Database Error: {str(e)}'}), 500
        
        # Step 10: Update in-memory stores
        with store_lock:
            pipeline_store[g.user_id] = pipeline
            profile_store[g.user_id] = {
                'profile_data': parsed,
                'raw_profile': profile_data,
                'cv_filename': filename,
                'cv_content': cv_content,
                'cv_file_id': cv_file_id
            }
        
        return jsonify({
            'success': True, 
            'profile': parsed, 
            'cv_filename': filename,
            'idempotent': False
        })
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        return jsonify({'success': False, 'error': 'CV file not found or could not be read'}), 400
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing CV: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Failed to process CV: {str(e)}'}), 500

@profile_bp.route('/regenerate-cv', methods=['POST'])
@login_required
def regenerate_cv():
    """
    Regenerate and optimize CV to increase match score.
    Uses AI to inject keywords, reframe experience, and optimize for 2025 hiring trends.
    """
    try:
        tablesDB = TablesDB(g.client)
        
        # Step 1: Get current profile and CV content
        result = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.equal('is_active', True),
                Query.limit(1),
            ],
        )
        if result.get('total', 0) == 0:
            result = tablesDB.list_rows(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                queries=[
                    Query.equal('userId', g.user_id),
                    Query.order_desc('$updatedAt'),
                    Query.limit(1),
                ],
            )
        
        if result.get('total', 0) == 0:
            return jsonify({
                'success': False,
                'error': 'No profile found. Please upload a CV first.'
            }), 404
        
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        if not rows:
            return jsonify({
                'success': False,
                'error': 'No profile found. Please upload a CV first.'
            }), 404
        
        doc = rows[0]
        
        # Get CV content - try cv_text field first, then rehydrate from pipeline
        cv_content = doc.get('cv_text') or ''
        logger.info(f"Initial cv_content from doc: {len(cv_content) if cv_content else 0} chars")
        
        if not cv_content:
            # Try to rehydrate pipeline to get CV content
            logger.info("CV text not in doc, attempting rehydration...")
            pipeline = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            if pipeline:
                # Check profile_store first (rehydration should populate this)
                p_info = profile_store.get(g.user_id)
                if p_info and p_info.get('cv_content'):
                    cv_content = p_info['cv_content']
                    logger.info(f"Got CV content from profile_store: {len(cv_content)} chars")
                # If still not found, try to load from pipeline's cv_path
                elif hasattr(pipeline, 'cv_path') and pipeline.cv_path and os.path.exists(pipeline.cv_path):
                    try:
                        logger.info(f"Attempting to load CV from pipeline path: {pipeline.cv_path}")
                        cv_content = pipeline.load_cv()
                        logger.info(f"Loaded CV content from pipeline file: {len(cv_content)} chars")
                    except Exception as e:
                        logger.warning(f"Failed to load CV from pipeline path {pipeline.cv_path}: {e}")
                # Also check if pipeline has cv_content attribute directly
                elif hasattr(pipeline, 'cv_content') and pipeline.cv_content:
                    cv_content = pipeline.cv_content
                    logger.info(f"Got CV content from pipeline.cv_content: {len(cv_content)} chars")
            else:
                logger.warning("Rehydration returned None - could not rehydrate pipeline")
        
        # Fallback 1: Check in-memory profile_store (might have CV from previous session)
        if not cv_content:
            p_info = profile_store.get(g.user_id)
            if p_info and p_info.get('cv_content'):
                cv_content = p_info['cv_content']
                logger.info(f"Got CV content from in-memory profile_store: {len(cv_content)} chars")
        
        # Fallback 2: Try to load from local disk using cv_filename
        if not cv_content:
            cv_filename = doc.get('cv_filename')
            if cv_filename:
                local_cv_path = os.path.join(Config.UPLOAD_FOLDER, f"{g.user_id}_{cv_filename}")
                logger.info(f"Checking for local CV file: {local_cv_path}")
                if os.path.exists(local_cv_path) and os.path.getsize(local_cv_path) > 1024:
                    try:
                        logger.info(f"Found local CV file, loading content...")
                        pipeline_temp = JobApplicationPipeline(cv_path=local_cv_path)
                        cv_content = pipeline_temp.load_cv()
                        if cv_content and len(cv_content) > 100:
                            logger.info(f"Loaded CV content from local file: {len(cv_content)} chars")
                        else:
                            logger.warning(f"Local CV file content too short: {len(cv_content) if cv_content else 0} chars")
                            cv_content = None
                    except Exception as e:
                        logger.error(f"Failed to load CV from local file {local_cv_path}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    logger.info(f"Local CV file not found or too small: exists={os.path.exists(local_cv_path) if cv_filename else False}")
        
        # Fallback 3: Try to download from storage using file_id
        if not cv_content:
            file_id = doc.get('cv_file_id')
            logger.info(f"Final fallback: file_id={file_id}")
            if file_id:
                try:
                    logger.info(f"Attempting to download CV file {file_id} from bucket {Config.BUCKET_ID_CVS} as final fallback...")
                    storage = Storage(g.client)
                    tmp_dir = Config.UPLOAD_FOLDER
                    os.makedirs(tmp_dir, exist_ok=True)
                    tmp_name = f"regenerate_{g.user_id}_{file_id}.pdf"
                    cv_path = os.path.join(tmp_dir, tmp_name)
                    
                    # Check if file already exists
                    if os.path.exists(cv_path) and os.path.getsize(cv_path) > 1024:
                        logger.info(f"Using existing file: {cv_path}")
                    else:
                        logger.info(f"Downloading file {file_id}...")
                        data = storage.get_file_download(bucket_id=Config.BUCKET_ID_CVS, file_id=file_id)
                        with open(cv_path, 'wb') as f:
                            f.write(data)
                        logger.info(f"Downloaded {len(data)} bytes to {cv_path}")
                    
                    pipeline_temp = JobApplicationPipeline(cv_path=cv_path)
                    cv_content = pipeline_temp.load_cv()
                    if cv_content and len(cv_content) > 100:
                        logger.info(f"Loaded CV content from downloaded file: {len(cv_content)} chars")
                    else:
                        logger.error(f"Loaded CV content is too short: {len(cv_content) if cv_content else 0} chars")
                        cv_content = None
                except Exception as e:
                    logger.error(f"Failed to download and load CV file {file_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning("No file_id found in profile document")
        
        if not cv_content:
            logger.error(f"CV content not found for user {g.user_id}. Profile exists but cv_text is empty, rehydration failed, and file download failed.")
            return jsonify({
                'success': False,
                'error': 'CV content not found. Please re-upload your CV.'
            }), 404
        
        # Step 2: Get profile data
        def _sj(f, d):
            return _safe_json(f, d, doc)
        
        profile_data = {
            'name': doc.get('name') or '',
            'email': doc.get('email') or '',
            'phone': doc.get('phone') or '',
            'location': doc.get('location') or '',
            'skills': _sj('skills', []),
            'experience_level': doc.get('experience_level') or 'Entry Level',
            'education': _sj('education', []),
            'work_experience': _sj('work_experience', []),
            'strengths': _sj('strengths', []),
            'career_goals': doc.get('career_goals') or '',
        }
        
        # Step 3: Get sample job matches to understand target roles and keywords
        matches_sample = []
        try:
            mq = [
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt'),
                Query.limit(1),
            ]
            mres = tablesDB.list_rows(
                Config.DATABASE_ID, Config.COLLECTION_ID_MATCHES, queries=mq
            )
            if mres.get('total', 0) > 0:
                # TablesDB returns 'rows' instead of 'documents' in the new API
                match_rows = mres.get('rows', mres.get('documents', []))
                if match_rows:
                    raw = match_rows[0].get('matches', '[]') or '[]'
                    matches_sample = json.loads(raw) if isinstance(raw, str) else raw
                    if not isinstance(matches_sample, list):
                        matches_sample = []
        except Exception as e:
            logger.debug(f"Could not fetch matches for regeneration: {e}")
        
        # Extract target roles and keywords from matches
        target_roles = []
        job_keywords_list = []
        for match in matches_sample[:10]:  # Use top 10 matches
            job = match.get('job') or match
            if job.get('title'):
                target_roles.append(job.get('title'))
            if job.get('description'):
                # Extract keywords from description (simple approach)
                desc = job.get('description', '').lower()
                # Common tech keywords
                tech_keywords = ['python', 'javascript', 'react', 'node', 'sql', 'aws', 'azure', 
                               'docker', 'kubernetes', 'api', 'rest', 'graphql', 'typescript',
                               'machine learning', 'ai', 'data science', 'agile', 'scrum']
                for kw in tech_keywords:
                    if kw in desc and kw not in job_keywords_list:
                        job_keywords_list.append(kw)
        
        # Step 4: Use application_writer to optimize CV for score improvement
        try:
            try:
                from agents import application_writer
            except ImportError as e:
                logger.error(f"Failed to import application_writer: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Missing dependency: application_writer agent. {str(e)}'
                }), 500
            
            try:
                from utils.scraping import extract_job_keywords
            except ImportError as e:
                logger.error(f"Failed to import extract_job_keywords: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Missing dependency: extract_job_keywords. {str(e)}'
                }), 500
            
            # Create a synthetic job posting based on target roles and trends
            synthetic_job = {
                'title': target_roles[0] if target_roles else profile_data.get('experience_level', 'Software Developer'),
                'company': 'Target Roles',
                'description': f"""
                We are looking for a {profile_data.get('experience_level', 'professional')} with expertise in:
                {', '.join(job_keywords_list[:15]) if job_keywords_list else 'modern software development'}
                
                Key requirements for 2025:
                - Strong technical skills in current industry-standard technologies
                - Proven track record with quantified achievements
                - Experience with modern development practices and tools
                - Ability to work in agile environments
                - Strong problem-solving and communication skills
                """
            }
            
            # Extract keywords from synthetic job
            job_keywords = extract_job_keywords(synthetic_job.get('description', ''))
            
            # Use application_writer to optimize CV
            optimization_prompt = f"""
            Optimize this CV to increase the candidate's match score for their target roles.
            
            Current CV Content:
            {cv_content[:5000]}  # Limit to avoid token issues
            
            Candidate Profile:
            - Name: {profile_data.get('name', 'Candidate')}
            - Experience Level: {profile_data.get('experience_level', 'Entry Level')}
            - Skills: {', '.join(profile_data.get('skills', [])[:20])}
            - Career Goals: {profile_data.get('career_goals', '')[:500]}
            
            Target Roles: {', '.join(target_roles[:5]) if target_roles else 'Software Development roles'}
            Industry Keywords: {', '.join(job_keywords_list[:20]) if job_keywords_list else 'Modern software development'}
            
            Optimization Goals:
            1. Inject relevant keywords naturally throughout the CV
            2. Reframe experience to match 2025 hiring trends
            3. Quantify achievements where possible
            4. Enhance professional summary to align with target roles
            5. Optimize for ATS compatibility (score 85+)
            
            Return a JSON object with:
            {{
                "optimized_cv": "Full optimized CV content",
                "ats_score": 85,
                "improvements_made": ["List of improvements"],
                "keyword_matches": ["Keywords added"],
                "score_breakdown": {{
                    "keyword_match": 28,
                    "quantified_achievements": 22,
                    "skills_alignment": 18,
                    "experience_relevance": 12,
                    "format_quality": 9
                }}
            }}
            """
            
            try:
                result = application_writer.run(optimization_prompt)
                
                # Extract content from RunOutput object
                result_text = result.content if hasattr(result, 'content') else str(result)
                
                # Parse the result
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        optimized_data = json.loads(json_match.group(0))
                        optimized_cv = optimized_data.get('optimized_cv', cv_content)
                        improvements = optimized_data.get('improvements_made', [])
                        keyword_matches = optimized_data.get('keyword_matches', [])
                        ats_score = optimized_data.get('ats_score', 0)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from agent response: {e}")
                        # Fallback: use the result as-is
                        optimized_cv = result_text
                        improvements = ["CV optimized with AI"]
                        keyword_matches = []
                        ats_score = 0
                else:
                    # Fallback: use the result as-is
                    optimized_cv = result_text
                    improvements = ["CV optimized with AI"]
                    keyword_matches = []
                    ats_score = 0
            except Exception as api_error:
                logger.error(f"Error during CV optimization: {api_error}")
                import traceback
                logger.error(traceback.format_exc())
                # Return error response
                return jsonify({
                    'success': False,
                    'error': f'CV optimization failed: {str(api_error)}. Please check your API key and try again.'
                }), 500
            
            # Step 5: Update profile with optimized CV content
            try:
                tablesDB.update_row(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    doc['$id'],
                    data={
                        'cv_text': optimized_cv[:50000]  # Limit size
                    }
                )
                
                # Update pipeline store
                with store_lock:
                    if g.user_id in pipeline_store:
                        pipeline = pipeline_store[g.user_id]
                        pipeline.cv_content = optimized_cv
                    if g.user_id in profile_store:
                        profile_store[g.user_id]['cv_content'] = optimized_cv
                
                logger.info(f"CV regenerated and saved for user {g.user_id}")
                
            except Exception as e:
                logger.warning(f"Failed to save optimized CV to database: {e}")
                # Continue anyway - we still return the optimized content
            
            return jsonify({
                'success': True,
                'optimized_cv': optimized_cv,
                'improvements_made': improvements,
                'keyword_matches': keyword_matches,
                'ats_score': ats_score,
                'message': f'CV optimized successfully. Injected {len(keyword_matches)} keywords and improved ATS score.'
            })
            
        except Exception as e:
            logger.error(f"Error during CV optimization: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to optimize CV: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error regenerating CV: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to regenerate CV: {str(e)}'
        }), 500

@profile_bp.route('/<profile_id>/active', methods=['PUT'])
@login_required
def set_active_profile(profile_id):
    """Set a specific profile as active"""
    try:
        tablesDB = TablesDB(g.client)
        
        # Verify profile ownership
        try:
            doc = tablesDB.get_row(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                profile_id
            )
            if doc.get('userId') != g.user_id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        except Exception:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
        # Set active exclusive
        _set_active_exclusive(tablesDB, g.user_id, profile_id)
        
        return jsonify({'success': True, 'message': 'Profile set as active'})
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/list', methods=['GET'])
@login_required
def list_profiles():
    """List all CV profiles for the current user"""
    try:
        tablesDB = TablesDB(g.client)
        result = tablesDB.list_rows(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$updatedAt')
            ]
        )
        
        profiles = []
        # TablesDB returns 'rows' instead of 'documents' in the new API
        rows = result.get('rows', result.get('documents', []))
        for doc in rows:
            profiles.append({
                '$id': doc.get('$id'),
                'cv_file_id': doc.get('cv_file_id'),
                'cv_filename': doc.get('cv_filename', 'CV.pdf'),
                '$createdAt': doc.get('$createdAt'),
                '$updatedAt': doc.get('$updatedAt'),
                'name': doc.get('name', ''),
                'email': doc.get('email', ''),
                'is_active': doc.get('is_active', False)
            })
        
        return jsonify({'success': True, 'profiles': profiles})
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        return jsonify({'success': False, 'error': str(e), 'profiles': []}), 500

@profile_bp.route('/profile/<profile_id>', methods=['DELETE'])
@login_required
def delete_profile(profile_id):
    """Delete a CV profile and associated storage file"""
    try:
        tablesDB = TablesDB(g.client)
        storage = Storage(g.client)
        
        # Get the profile document
        try:
            doc = tablesDB.get_row(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                profile_id
            )
        except Exception as e:
            logger.error(f"Profile not found: {e}")
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
        
        # Verify ownership
        if doc.get('userId') != g.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete file from Appwrite storage if exists
        cv_file_id = doc.get('cv_file_id')
        if cv_file_id:
            try:
                storage.delete_file(Config.BUCKET_ID_CVS, cv_file_id)
                logger.info(f"Deleted CV file from storage: {cv_file_id}")
            except Exception as e:
                # CRITICAL FIX: Don't stop deletion if file is missing
                logger.warning(f"Failed to delete file from storage (might be missing): {e}")
                
        # Delete local file if exists
        cv_filename = doc.get('cv_filename')
        if cv_filename:
            local_path = os.path.join(Config.UPLOAD_FOLDER, f"{g.user_id}_{cv_filename}")
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    logger.info(f"Deleted local CV file: {local_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete local file: {e}")
        
        # Delete profile document - This MUST happen even if storage delete failed
        try:
            tablesDB.delete_row(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                profile_id
            )
        except Exception as e:
             logger.error(f"Failed to delete database document: {e}")
             return jsonify({'success': False, 'error': f'Failed to delete profile record: {str(e)}'}), 500
        
        # Clean up in-memory stores if this was the active profile
        with store_lock:
            if g.user_id in profile_store:
                stored_profile = profile_store[g.user_id]
                if stored_profile.get('cv_file_id') == cv_file_id:
                    # Clear stores if this was the active profile
                    profile_store.pop(g.user_id, None)
                    pipeline_store.pop(g.user_id, None)
        
        logger.info(f"Deleted profile {profile_id} for user {g.user_id}")
        return jsonify({'success': True, 'message': 'Profile deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting profile: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/storage/download', methods=['GET'])
@login_required
def storage_download():
    try:
        bucket_id = request.args.get('bucket_id')
        file_id = request.args.get('file_id')
        if not bucket_id or not file_id: return jsonify({'error': 'Missing parameters'}), 400
        
        project_id = Config.APPWRITE_PROJECT_ID
        endpoint = Config.APPWRITE_ENDPOINT
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header else None
        
        url = f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/download"
        headers = {'X-Appwrite-Project': project_id, 'X-Appwrite-JWT': token}
        
        r = _req.get(url, headers=headers, stream=True)
        if r.status_code != 200: return jsonify({'error': 'Download failed'}), r.status_code
        
        def generate():
            for chunk in r.iter_content(chunk_size=8192): yield chunk
        
        return Response(generate(), headers={'Content-Disposition': f'attachment; filename="download"'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
