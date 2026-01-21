"""
Database-Backed Task Manager Service
Implements a 'Poor Man's Task Queue' using Appwrite Database.
Monitors job states, handles timeouts, and ensures resilience.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from appwrite.services.databases import Databases
from appwrite.client import Client
from appwrite.query import Query
from config import Config

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self.client = Client()
        self.client.set_endpoint(Config.APPWRITE_ENDPOINT)
        self.client.set_project(Config.APPWRITE_PROJECT_ID)
        self.client.set_key(Config.APPWRITE_API_KEY)
        self.db = Databases(self.client)
        self.active_tasks = 0
        self.total_tasks_processed = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Start the task manager background thread"""
        if self._thread and self._thread.is_alive():
            return
            
        logger.info("Starting Task Manager Service...")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the task manager"""
        logger.info("Stopping Task Manager Service...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def submit_task(self, target, args=(), kwargs=None, daemon=True):
        """
        Submit a task to be run in a background thread.
        This centralized method allows for future scaling (e.g., Celery) without changing call sites.
        """
        if kwargs is None: kwargs = {}
        
        def wrapped_target(*args, **kwargs):
            with self.lock:
                self.active_tasks += 1
                self.total_tasks_processed += 1
            try:
                target(*args, **kwargs)
            finally:
                with self.lock:
                    self.active_tasks -= 1

        t = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs, daemon=daemon)
        t.start()
        return t

    def get_system_stats(self):
        """Get system health statistics"""
        return {
            "active_threads": self.active_tasks,
            "total_processed": self.total_tasks_processed,
            "status": "healthy" if not self._stop_event.is_set() else "stopped"
        }
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self._check_stale_jobs()
            except Exception as e:
                logger.error(f"Error in Task Manager loop: {e}")
            
            # Sleep for 60 seconds
            if self._stop_event.wait(60):
                break

    def _check_stale_jobs(self):
        """Check for jobs that have timed out"""
        try:
            # Calculate timeout threshold (10 minutes ago)
            # Appwrite queries are limited, so we might need to fetch processing jobs and check timestamps
            # Query for 'processing' or 'initializing' status
            queries = [
                Query.equal('status', ['processing', 'initializing']),
                Query.limit(100)
            ]
            
            result = self.db.list_documents(
                Config.DATABASE_ID, 
                Config.COLLECTION_ID_JOBS, 
                queries=queries
            )
            
            timeout_threshold = time.time() - 900 # 15 minutes (increased from 10m)
            
            for doc in result['documents']:
                updated_at_str = doc.get('$updatedAt', '')
                # Parse ISO string
                try:
                    # simplistic parsing, usually "2023-01-01T12:00:00.000+00:00"
                    # We can also rely on our own 'progress' updates if we stored a timestamp there
                    # But Appwrite's $updatedAt is reliable
                    if updated_at_str:
                        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        if updated_at.timestamp() < timeout_threshold:
                            self._fail_job(doc['$id'], "Job timed out (stuck for > 10 minutes)")
                except Exception as e:
                    logger.warning(f"Error checking job {doc['$id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking stale jobs: {e}")

    def _fail_job(self, job_id, reason):
        """Mark a job as failed"""
        try:
            logger.warning(f"Marking job {job_id} as failed: {reason}")
            self.db.update_document(
                Config.DATABASE_ID,
                Config.COLLECTION_ID_JOBS,
                job_id,
                data={
                    'status': 'error',
                    'error': reason,
                    'progress': 0
                }
            )
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")

# Global instance
task_manager = TaskManager()
