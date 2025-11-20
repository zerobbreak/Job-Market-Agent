"""
Memory Store Utility
Handles long-term memory using ChromaDB.
Stores job history and user preferences.
"""

import os
import logging
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client"""
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collections
        self.jobs_collection = self.client.get_or_create_collection(
            name="job_history",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.user_prefs_collection = self.client.get_or_create_collection(
            name="user_preferences",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Memory Store initialized at {persist_directory}")

    def save_job(self, job_data: Dict[str, Any]):
        """
        Save a job to history.
        """
        try:
            job_id = str(job_data.get('id') or job_data.get('job_id') or hash(job_data.get('title', '') + job_data.get('company', '')))
            
            # Create a text representation for embedding
            document = f"{job_data.get('title', '')} at {job_data.get('company', '')}. " \
                       f"{job_data.get('description', '')} " \
                       f"Location: {job_data.get('location', '')}"
            
            self.jobs_collection.upsert(
                ids=[job_id],
                documents=[document],
                metadatas=[{
                    "title": job_data.get('title', ''),
                    "company": job_data.get('company', ''),
                    "location": job_data.get('location', ''),
                    "date_added": datetime.now().isoformat(),
                    "source": job_data.get('job_url', 'unknown')
                }]
            )
            logger.info(f"Saved job: {job_data.get('title')} at {job_data.get('company')}")
            
        except Exception as e:
            logger.error(f"Error saving job: {e}")

    def find_similar_jobs(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar jobs in history.
        """
        try:
            results = self.jobs_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            jobs = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    jobs.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    })
            return jobs
            
        except Exception as e:
            logger.error(f"Error finding jobs: {e}")
            return []

    def log_user_feedback(self, job_id: str, action: str, reason: str = ""):
        """
        Log user feedback (Applied, Rejected, Liked, Disliked).
        """
        try:
            feedback_id = f"{job_id}_{action}_{datetime.now().timestamp()}"
            
            self.user_prefs_collection.add(
                ids=[feedback_id],
                documents=[f"User {action} job {job_id}. Reason: {reason}"],
                metadatas=[{
                    "job_id": job_id,
                    "action": action,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                }]
            )
            logger.info(f"Logged feedback: {action} for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error logging feedback: {e}")

    def get_user_preferences(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent user preferences/actions.
        """
        try:
            # Since we can't easily "get all", we query for generic terms or just peek
            # For now, let's just get the last few items if possible, or query for "Applied"
            results = self.user_prefs_collection.query(
                query_texts=["User liked or applied"],
                n_results=n_results
            )
            
            prefs = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    prefs.append({
                        "action": results['metadatas'][0][i].get('action'),
                        "reason": results['metadatas'][0][i].get('reason'),
                        "document": results['documents'][0][i]
                    })
            return prefs
            
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return []

# Global instance
memory = MemoryStore()
