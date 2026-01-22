from flask import Blueprint, request, jsonify, g, send_file, Response
from routes.auth_routes import login_required
from services.pipeline_service import (
    JobApplicationPipeline, 
    _rehydrate_pipeline_from_profile,
    parse_profile,
    pipeline_store,
    profile_store,
    store_lock
)
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from appwrite.id import ID
from config import Config
from werkzeug.utils import secure_filename
import json
import logging
import os
import hashlib
from datetime import datetime
import requests as _req

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

@profile_bp.route('/current', methods=['GET'])
@login_required
def get_current_profile():
    try:
        databases = Databases(g.client)
        # 1. Try to find explicitly active profile
        result = databases.list_documents(
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
            result = databases.list_documents(
                Config.DATABASE_ID, 
                Config.COLLECTION_ID_PROFILES, 
                queries=[
                    Query.equal('userId', g.user_id), 
                    Query.order_desc('$updatedAt'),
                    Query.limit(1)
                ]
            )
            
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
            
        doc = result['documents'][0]
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
        databases = Databases(g.client)
        result = databases.list_documents(Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, queries=[Query.equal('userId', g.user_id), Query.limit(1)])
        if result.get('total', 0) == 0: return jsonify({'success': False, 'error': 'No profile found'}), 404
        doc = result['documents'][0]
        
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
                    databases.update_document(Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, doc['$id'], data={'name': profile['name'], 'email': profile['email']})
                except Exception: pass
                    
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        databases = Databases(g.client)
        result = databases.list_documents(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', g.user_id), Query.limit(1)]
        )
        
        if result.get('total', 0) == 0:
            return jsonify({
                'success': False, 
                'error': 'No profile found. Please upload a CV first.'
            }), 404
        
        doc = result['documents'][0]
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
            databases.update_document(
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
        updated_result = databases.get_document(
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

def _set_active_exclusive(databases, user_id, active_profile_id):
    """
    Sets the specified profile as active and ensures all other profiles 
    for the user are set to inactive.
    """
    try:
        # 1. Find currently active profiles for this user
        active_profiles = databases.list_documents(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', user_id),
                Query.equal('is_active', True)
            ]
        )
        
        # 2. Deactivate them (unless it's the target one)
        for doc in active_profiles['documents']:
            if doc['$id'] != active_profile_id:
                databases.update_document(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    doc['$id'],
                    data={'is_active': False}
                )
                logger.info(f"Deactivated profile {doc['$id']}")
        
        # 3. Activate the target profile
        # We do this unconditionally to ensure it's set to True
        databases.update_document(
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
        databases = Databases(g.client)
        storage = Storage(g.client)
        
        existing_profiles = databases.list_documents(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', g.user_id)]
        )
        
        existing_profile = None
        if existing_profiles.get('total', 0) > 0:
            for doc in existing_profiles.get('documents', []):
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
            with open(cv_path, 'rb') as f:
                cv_file_id = storage.create_file(
                    bucket_id=Config.BUCKET_ID_CVS,
                    file_id=ID.unique(),
                    file=f,
                    permissions=[f"read({g.user_id})"]
                )['$id']
            logger.info(f"CV saved to Appwrite storage: {cv_file_id}")
        except Exception as e:
            logger.warning(f"Failed to save CV to Appwrite storage: {e}")
            # Continue without storage - file is still on disk
        
        # Step 9: Save profile to database
        try:
            # Prepare data with new inferred fields
            seniority = parsed.get('seniority') or parsed.get('experience_level', '')
            
            # Format suggested roles as career goals if available
            career_goals = parsed.get('career_goals', '')
            suggested_roles = parsed.get('suggested_roles', [])
            if not career_goals and suggested_roles:
                career_goals = ", ".join(suggested_roles)
            elif suggested_roles:
                # Append if both exist
                career_goals = f"{career_goals}. Suggested: {', '.join(suggested_roles)}"
            
            profile_data_for_db = {
                'userId': g.user_id,
                'name': parsed.get('name', ''),
                'email': parsed.get('email', ''),
                'phone': parsed.get('phone', ''),
                'location': parsed.get('location', ''),
                'skills': json.dumps(parsed.get('skills', [])),
                'experience_level': seniority,
                'education': json.dumps(parsed.get('education', [])),
                # 'work_experience' removed as it's not in schema
                # 'projects': json.dumps(parsed.get('projects', [])), # projects also not in schema dump
                'strengths': json.dumps(parsed.get('key_strengths') or parsed.get('strengths', [])),
                'career_goals': career_goals,
                'cv_filename': filename,
                'cv_hash': file_hash,
                'cv_file_id': cv_file_id,
                # 'cv_text': cv_content[:50000] if len(cv_content) > 50000 else cv_content  # Limit text size - REMOVED: Not in schema
            }
            
            # Update existing profile or create new one
            final_profile_id = None
            if existing_profile:
                final_profile_id = existing_profile['$id']
                databases.update_document(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    final_profile_id,
                    data=profile_data_for_db
                )
                logger.info(f"Updated existing profile for user={g.user_id}")
            else:
                new_doc = databases.create_document(
                    Config.DATABASE_ID,
                    Config.COLLECTION_ID_PROFILES,
                    document_id=ID.unique(),
                    data=profile_data_for_db
                )
                final_profile_id = new_doc['$id']
                logger.info(f"Created new profile for user={g.user_id}")
            
            # Set as active
            _set_active_exclusive(databases, g.user_id, final_profile_id)
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

@profile_bp.route('/<profile_id>/active', methods=['PUT'])
@login_required
def set_active_profile(profile_id):
    """Set a specific profile as active"""
    try:
        databases = Databases(g.client)
        
        # Verify profile ownership
        try:
            doc = databases.get_document(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_PROFILES,
                profile_id
            )
            if doc.get('userId') != g.user_id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        except Exception:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
        # Set active exclusive
        _set_active_exclusive(databases, g.user_id, profile_id)
        
        return jsonify({'success': True, 'message': 'Profile set as active'})
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/profile/list', methods=['GET', 'OPTIONS'])
@login_required
def list_profiles():
    """List all CV profiles for the current user"""
    try:
        databases = Databases(g.client)
        result = databases.list_documents(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$updatedAt')
            ]
        )
        
        profiles = []
        for doc in result.get('documents', []):
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
        databases = Databases(g.client)
        storage = Storage(g.client)
        
        # Get the profile document
        try:
            doc = databases.get_document(
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
            databases.delete_document(
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

@profile_bp.route('/improve-text', methods=['POST'])
@login_required
def improve_text():
    """
    Improve specific text sections of the CV using AI.
    """
    try:
        data = request.get_json()
        text = data.get('text')
        section = data.get('section', 'general') # e.g. 'summary', 'experience'
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        # Import inside function to avoid circular imports if any
        from agents import application_writer
        
        prompt = f"""
        Act as an expert CV writer. Improve the following {section} text to be more impactful, professional, and result-oriented.
        Use active verbs and quantifiable metrics where possible. Keep it concise.
        
        Original Text:
        "{text}"
        
        Return ONLY the improved text. Do not add any conversational filler like "Here is the improved text".
        """
        
        improved = application_writer.run(prompt)
        
        # Clean up response
        clean_text = improved.content if hasattr(improved, 'content') else str(improved)
        # Remove any surrounding quotes if present
        clean_text = clean_text.strip().strip('"').strip("'")
        
        return jsonify({'success': True, 'improved_text': clean_text})
    except Exception as e:
        logger.error(f"Error improving text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
