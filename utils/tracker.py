import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class ApplicationTracker:
    """
    Tracks job applications using a local SQLite database.
    """
    
    def __init__(self, db_path: str = "applications.db"):
        """
        Initialize the tracker with a database path.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Initialize the database schema if it doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_url TEXT,
            location TEXT,
            status TEXT DEFAULT 'generated',
            date_created DATETIME,
            date_updated DATETIME,
            cv_path TEXT,
            cover_letter_path TEXT,
            job_description TEXT,
            match_score INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_application(self, job_data: Dict[str, Any], cv_path: str, cover_letter_path: Optional[str] = None) -> int:
        """
        Add a new application record.
        
        Args:
            job_data: Dictionary containing job details (company, title, url, etc.)
            cv_path: Path to the generated CV file
            cover_letter_path: Path to the generated cover letter file (optional)
            
        Returns:
            int: The ID of the new application record
        """
        # 1. Save to Local SQLite (Legacy/Offline support)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO applications (
            company, role, job_url, location, status, 
            date_created, date_updated, cv_path, cover_letter_path, 
            job_description, match_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_data.get('company', 'Unknown'),
            job_data.get('title', 'Unknown'),
            job_data.get('job_url', ''),
            job_data.get('location', ''),
            'generated',
            now,
            now,
            cv_path,
            cover_letter_path,
            job_data.get('description', ''),
            job_data.get('match_score', 0)
        ))
        
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 2. Sync to Appwrite (if enabled)
        try:
            from .appwrite_client import AppwriteService
            appwrite = AppwriteService()
            
            if appwrite.enabled:
                print("☁️ Syncing to Appwrite...")
                
                # Upload files
                cv_file_id = appwrite.upload_file(cv_path)
                cl_file_id = None
                if cover_letter_path and os.path.exists(cover_letter_path):
                    cl_file_id = appwrite.upload_file(cover_letter_path)
                
                # Create DB Record
                # TODO: Get actual user_id from session/auth context. 
                # For now using a placeholder or 'anonymous'
                user_id = 'anonymous_user' 
                
                appwrite_id = appwrite.save_application(
                    user_id=user_id,
                    job_data=job_data,
                    cv_file_id=cv_file_id,
                    cl_file_id=cl_file_id
                )
                print(f"✓ Synced to Appwrite (ID: {appwrite_id})")
                
        except Exception as e:
            print(f"⚠️ Failed to sync to Appwrite: {e}")
        
        print(f"✓ Application tracked: {job_data.get('company')} - {job_data.get('title')} (ID: {app_id})")
        return app_id

    def update_status(self, app_id: int, new_status: str):
        """
        Update the status of an application.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE applications 
        SET status = ?, date_updated = ?
        WHERE id = ?
        ''', (new_status, datetime.now().isoformat(), app_id))
        
        conn.commit()
        conn.close()

    def get_applications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve applications, optionally filtered by status.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM applications WHERE status = ? ORDER BY date_created DESC', (status,))
        else:
            cursor.execute('SELECT * FROM applications ORDER BY date_created DESC')
            
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, int]:
        """
        Get application statistics.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
        stats = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM applications')
        stats['total'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
