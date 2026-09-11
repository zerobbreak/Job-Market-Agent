"""
Persistent Job Store for Apply with AI Preview Jobs, backed by Postgres.
Implements battle-tested patterns: persistent state, auto-resume, granular progress tracking,
and Application Tracking and Analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.core.config import get_settings
from app.repositories.application_repo import ApplicationRepository
from app.repositories.job_repo import JobRepository
from app.repositories.query import Query
from app.repositories.storage_repo import StorageRepository

logger = logging.getLogger(__name__)

settings = get_settings()

_jobs_repo = JobRepository(settings)
_applications_repo = ApplicationRepository(settings)
_storage_repo = StorageRepository(settings)

# --- Helper Functions ---

def _serialize_data(data):
    """Safely serialize data for storage"""
    return _jobs_repo._serialize(data)

def _deserialize_data(data):
    """Safely deserialize data from storage"""
    return _jobs_repo._deserialize(data)

def _upload_file(file_path: str) -> Optional[str]:
    """Upload a file to storage and return its file id"""
    if not file_path:
        return None
    return _storage_repo.upload_file(file_path, bucket_id="applications")

# --- Job State Management (Existing) ---

def save_job_state(job_id: str, state: dict) -> bool:
    """Save job processing state"""
    try:
        job_info = state.get('job_data')
        if isinstance(job_info, dict):
            title = job_info.get('title', 'Untitled')
            company = job_info.get('company', 'Unknown Company')
        else:
            title = "Preview Job"
            company = "Preview Company"

        data = {
            'title': title[:255],
            'company': company[:255],
            'status': state.get('status', 'initializing'),
            'progress': int(state.get('progress', 0)),
            'phase': state.get('phase', ''),
            'job_data': _serialize_data(state.get('job_data')),
            'result': _serialize_data(state.get('result')),
            'template_type': state.get('template_type', 'modern'),
            'user_id': state.get('user_id', ''),
            'error': state.get('error', '')
        }

        if _jobs_repo.get(job_id):
            _jobs_repo.update(job_id, data)
        else:
            _jobs_repo.create(data, document_id=job_id)

        return True
    except Exception as e:
        logger.error(f"Failed to save job state for {job_id}: {e}")
        return False

def load_job_state(job_id: str) -> dict | None:
    """Load job processing state"""
    try:
        doc = _jobs_repo.get(job_id)
        if not doc:
            return None

        updated_at_str = doc.get('$updatedAt')
        return {
            'status': doc.get('status'),
            'progress': doc.get('progress'),
            'phase': doc.get('phase'),
            'job_data': _deserialize_data(doc.get('job_data')),
            'result': _deserialize_data(doc.get('result')),
            'template_type': doc.get('template_type'),
            'user_id': doc.get('user_id'),
            'error': doc.get('error'),
            'last_updated': datetime.fromisoformat(updated_at_str).timestamp() if updated_at_str else datetime.now().timestamp()
        }
    except Exception as e:
        logger.error(f"Failed to load job state for {job_id}: {e}")
        return None

def delete_job_state(job_id: str):
    """Delete job state"""
    try:
        _jobs_repo.delete(job_id)
    except Exception as e:
        logger.error(f"Failed to delete job state {job_id}: {e}")

def update_job_progress(job_id: str, progress: int, status: str = None, phase: str = None, error: str = None, result: dict = None):
    """Update job progress"""
    try:
        data = {'progress': int(progress)}
        if status: data['status'] = status
        if phase: data['phase'] = phase
        if error:
            data['error'] = error
            data['status'] = 'error'
        if result:
            data['result'] = _serialize_data(result)
            data['status'] = 'done'
            data['progress'] = 100

        if not _jobs_repo.update(job_id, data):
            raise RuntimeError(f"Job {job_id} not found for progress update")
        logger.info(f"Job {job_id}: {progress}% - {phase or status}")
    except Exception as e:
        logger.error(f"Failed to update progress for {job_id}: {e}")
        state = {'progress': progress, 'status': status, 'phase': phase, 'error': error, 'result': result}
        save_job_state(job_id, state)

def get_recent_failures(limit: int = 5) -> int:
    """Get count of recent consecutive failures"""
    try:
        queries = [Query.equal('status', 'error'), Query.order_desc('$createdAt'), Query.limit(limit)]
        return len(_jobs_repo.list(queries))
    except Exception:
        return 0

# --- Application Tracking & Analytics (New Migration) ---

def save_application(job_data: Dict[str, Any], cv_path: str, cover_letter_path: Optional[str] = None,
                     ats_score: Optional[int] = None, metadata_path: Optional[str] = None,
                     app_dir: Optional[str] = None, user_id: str = 'anonymous_user') -> Optional[str]:
    """
    Save a new application record.
    Migrated from ApplicationTracker.add_application.
    """
    try:
        # Upload files
        cv_file_id = _upload_file(cv_path)
        cl_file_id = _upload_file(cover_letter_path) if cover_letter_path else None

        now = datetime.now().isoformat()

        data = {
            'company': job_data.get('company', 'Unknown'),
            'role': job_data.get('title', 'Unknown'),  # Mapping 'title' to 'role'
            'job_url': job_data.get('url', ''),
            'location': job_data.get('location', ''),
            'status': 'generated',
            'date_created': now,
            'date_updated': now,
            'cv_storage_id': cv_file_id,
            'cover_letter_storage_id': cl_file_id,
            'job_description': job_data.get('description', '')[:10000] if job_data.get('description') else '',
            'match_score': int(job_data.get('relevance_score', 0)),
            'ats_score': ats_score,
            'metadata_path': metadata_path,
            'app_dir': app_dir,
            'user_id': user_id,
            'views': 0
        }

        result = _applications_repo.create(data)
        if not result:
            raise RuntimeError("Application create returned no result")

        logger.info(f"Application tracked: {data['company']} - {data['role']} (ID: {result['$id']})")
        return result['$id']

    except Exception as e:
        logger.error(f"Failed to save application: {e}")
        return None

def update_application_status(app_id: str, status: str, additional_data: Dict[str, Any] = None):
    """Update application status"""
    try:
        data = {
            'status': status,
            'date_updated': datetime.now().isoformat()
        }
        # Note: additional_data processing can be added here if schema permits

        _applications_repo.update(app_id, data)
    except Exception as e:
        logger.error(f"Failed to update application status {app_id}: {e}")

def get_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve applications"""
    try:
        queries = [Query.order_desc('date_created')]
        if status:
            queries.append(Query.equal('status', status))

        return _applications_repo.list(queries)
    except Exception as e:
        logger.error(f"Failed to get applications: {e}")
        return []

def get_application_stats() -> Dict[str, int]:
    """Get application statistics"""
    try:
        docs = _applications_repo.list([Query.limit(5000)])
        stats = {'total': len(docs)}
        for doc in docs:
            s = doc.get('status', 'unknown')
            stats[s] = stats.get(s, 0) + 1
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {'total': 0}

def get_engagement_analytics(days: int = 30) -> Dict[str, Any]:
    """Get engagement analytics (applications over time)"""
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        queries = [
            Query.greater_than_equal('date_created', cutoff),
            Query.limit(5000)
        ]
        rows = _applications_repo.list(queries)

        daily_counts = {}
        for doc in rows:
            # Assuming ISO format YYYY-MM-DD...
            date_str = doc['date_created'][:10]
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

        return {
            'total_applications': len(rows),
            'daily_activity': [{'date': k, 'count': v} for k, v in daily_counts.items()]
        }
    except Exception as e:
        logger.error(f"Failed to get engagement analytics: {e}")
        return {}

def get_application_heatmap() -> Dict[str, Any]:
    """Get application heatmap data (activity by day of week)"""
    try:
        rows = _applications_repo.list([Query.limit(5000)])
        heatmap = {}
        for doc in rows:
            try:
                dt = datetime.fromisoformat(doc['date_created'])
                day = dt.strftime('%A')
                heatmap[day] = heatmap.get(day, 0) + 1
            except Exception:
                pass

        return heatmap
    except Exception as e:
        logger.error(f"Failed to get heatmap: {e}")
        return {}

def track_view(app_id: str):
    """Increment view count for an application"""
    try:
        doc = _applications_repo.get(app_id)
        if not doc:
            return
        current_views = doc.get('views', 0) or 0
        _applications_repo.update(app_id, {'views': current_views + 1})
    except Exception as e:
        logger.error(f"Failed to track view for {app_id}: {e}")
