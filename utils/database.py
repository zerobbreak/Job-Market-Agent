"""
Database utilities for job storage and retrieval (No AI Required)
Uses SQLite for storage and TF-IDF for text similarity
"""

import sqlite3
import hashlib
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

class JobDatabase:
    """
    Job database with full-text search and similarity matching without AI
    Thread-safe using thread-local storage for connections
    """

    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        # Use thread-local storage for database connections
        self.local = threading.local()
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        self.tfidf_matrix = None
        self.job_ids = []
        # Initialize database schema in the current thread
        self.initialize_database()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.local.conn

    def initialize_database(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Main jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                url TEXT,
                source TEXT,
                posted_date TEXT,
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT,
                job_type TEXT,
                relevance_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Skills table (many-to-many relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_skills (
                job_id TEXT,
                skill_id INTEGER,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (skill_id) REFERENCES skills(id),
                PRIMARY KEY (job_id, skill_id)
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_title ON jobs(title)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_location ON jobs(location)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_posted_date ON jobs(posted_date)
        ''')
        
        # Note: Using LIKE queries instead of FTS5 for simpler maintenance

        conn.commit()
    
    def generate_job_id(self, job: Dict[str, Any]) -> str:
        """Generate unique ID for a job"""
        key = f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}|{job.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using keyword matching"""
        if not text:
            return []
        
        text_lower = text.lower()
        
        # Comprehensive skill list
        common_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 
            'go', 'rust', 'kotlin', 'swift', 'scala', 'r', 'matlab', 'perl',
            
            # Web Frameworks
            'react', 'angular', 'vue', 'svelte', 'node.js', 'express', 'django', 
            'flask', 'fastapi', 'spring', 'asp.net', 'laravel', 'rails',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sqlite', 'mariadb',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 
            'jenkins', 'github actions', 'gitlab', 'circleci', 'ansible',
            
            # Tools & Systems
            'git', 'linux', 'unix', 'windows', 'bash', 'powershell',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'devops', 'ci/cd', 'tdd', 'bdd',
            
            # Data & AI
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
            'data science', 'data analysis', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'spark', 'hadoop', 'tableau', 'power bi',
            
            # Web Technologies
            'html', 'css', 'sass', 'tailwind', 'bootstrap', 'webpack', 'rest api',
            'graphql', 'websockets', 'microservices',
            
            # Testing
            'testing', 'unit testing', 'integration testing', 'pytest', 'jest',
            'selenium', 'cypress',
            
            # Other
            'excel', 'powerpoint', 'word', 'jira', 'confluence', 'slack',
            'communication', 'leadership', 'teamwork', 'problem solving'
        ]
        
        found_skills = []
        for skill in common_skills:
            # Use word boundaries for better matching
            import re
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def store_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Store jobs in database with automatic duplicate handling
        Returns: number of jobs stored
        """
        stored_count = 0
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for job in jobs:
            try:
                # Generate unique ID
                job_id = job.get('id') or self.generate_job_id(job)
                
                # Extract skills
                description = job.get('description', f"{job.get('title', '')} at {job.get('company', '')}")
                skills = job.get('skills', [])
                if not skills:
                    skills = self.extract_skills(description)
                
                # Prepare salary info
                salary_info = job.get('salary_info', {})
                
                # Insert or replace job
                cursor.execute('''
                    INSERT OR REPLACE INTO jobs (
                        id, title, company, location, description, url, source,
                        posted_date, salary_min, salary_max, salary_currency,
                        job_type, relevance_score, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    job.get('title', 'Unknown'),
                    job.get('company', 'Unknown'),
                    job.get('location', 'Unknown'),
                    description,
                    job.get('url', ''),
                    job.get('source', 'unknown'),
                    job.get('date_posted') or job.get('posted_date') or datetime.now().isoformat(),
                    salary_info.get('salary_min'),
                    salary_info.get('salary_max'),
                    salary_info.get('salary_currency', 'USD'),
                    job.get('job_type', ''),
                    job.get('relevance_score', 0.0),
                    datetime.now().isoformat()
                ))
                
                # Store skills
                for skill in skills:
                    # Insert skill if doesn't exist
                    cursor.execute('''
                        INSERT OR IGNORE INTO skills (skill_name) VALUES (?)
                    ''', (skill.lower(),))
                    
                    # Get skill ID
                    cursor.execute('SELECT id FROM skills WHERE skill_name = ?', (skill.lower(),))
                    skill_id = cursor.fetchone()[0]
                    
                    # Link job to skill
                    cursor.execute('''
                        INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)
                    ''', (job_id, skill_id))
                
                # Note: Using LIKE queries for search, no FTS5 needed

                stored_count += 1
                
            except Exception as e:
                print(f"Error storing job {job.get('title', 'unknown')}: {e}")
                continue

        conn.commit()
        
        # Rebuild TF-IDF matrix after adding new jobs
        self._rebuild_tfidf_matrix()
        
        return stored_count
    
    def _rebuild_tfidf_matrix(self):
        """Rebuild TF-IDF matrix for similarity search"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, company, location, description FROM jobs')
        
        jobs = cursor.fetchall()
        if not jobs:
            return
        
        self.job_ids = [job['id'] for job in jobs]
        texts = [
            f"{job['title']} {job['company']} {job['location']} {job['description']}"
            for job in jobs
        ]
        
        if texts:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
    
    def search_jobs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for jobs using simple LIKE queries as fallback
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # For now, use simple LIKE search to avoid FTS5 issues
        # Split query into words and search for any match
        words = query.split()
        if not words:
            return []

        # Create LIKE conditions for each word
        like_conditions = []
        params = []
        for word in words[:3]:  # Limit to first 3 words to avoid too complex queries
            like_conditions.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
            word_param = f'%{word}%'
            params.extend([word_param, word_param, word_param])

        where_clause = ' OR '.join(like_conditions)

        sql = f'''
            SELECT * FROM jobs
            WHERE {where_clause}
            ORDER BY relevance_score DESC, posted_date DESC
            LIMIT ?
        '''
        params.append(limit)

        cursor.execute(sql, params)
        jobs = [dict(row) for row in cursor.fetchall()]

        # Add skills to each job
        for job in jobs:
            job['skills'] = self._get_job_skills(job['id'])

        return jobs

    # FTS5 methods removed - using LIKE queries instead

    def find_similar_jobs(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar jobs using TF-IDF cosine similarity
        """
        if self.tfidf_matrix is None or job_id not in self.job_ids:
            return []
        
        # Get index of the job
        job_index = self.job_ids.index(job_id)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(
            self.tfidf_matrix[job_index:job_index+1],
            self.tfidf_matrix
        )[0]
        
        # Get top similar jobs (excluding itself)
        similar_indices = np.argsort(similarities)[::-1][1:limit+1]
        similar_job_ids = [self.job_ids[i] for i in similar_indices]

        # Fetch job details
        conn = self._get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(similar_job_ids))
        cursor.execute(f'SELECT * FROM jobs WHERE id IN ({placeholders})', similar_job_ids)
        
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Add skills and similarity score
        for i, job in enumerate(jobs):
            job['skills'] = self._get_job_skills(job['id'])
            job['similarity_score'] = float(similarities[similar_indices[i]])
        
        return jobs
    
    def filter_jobs(self, **filters) -> List[Dict[str, Any]]:
        """
        Filter jobs by various criteria
        """
        query = 'SELECT * FROM jobs WHERE 1=1'
        params = []
        
        if 'title' in filters:
            query += ' AND title LIKE ?'
            params.append(f'%{filters["title"]}%')
        
        if 'company' in filters:
            query += ' AND company LIKE ?'
            params.append(f'%{filters["company"]}%')
        
        if 'location' in filters:
            query += ' AND location LIKE ?'
            params.append(f'%{filters["location"]}%')
        
        if 'min_salary' in filters:
            query += ' AND salary_min >= ?'
            params.append(filters['min_salary'])
        
        if 'min_relevance' in filters:
            query += ' AND relevance_score >= ?'
            params.append(filters['min_relevance'])
        
        if 'source' in filters:
            query += ' AND source = ?'
            params.append(filters['source'])
        
        query += ' ORDER BY relevance_score DESC, posted_date DESC'
        
        if 'limit' in filters:
            query += ' LIMIT ?'
            params.append(filters['limit'])

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Add skills and filter by required skills if specified
        for job in jobs:
            job['skills'] = self._get_job_skills(job['id'])
        
        if 'required_skills' in filters:
            required = [s.lower() for s in filters['required_skills']]
            jobs = [
                job for job in jobs
                if any(skill.lower() in [s.lower() for s in job['skills']] for skill in required)
            ]
        
        return jobs
    
    def _get_job_skills(self, job_id: str) -> List[str]:
        """Get skills for a specific job"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.skill_name FROM skills s
            JOIN job_skills js ON s.id = js.skill_id
            WHERE js.job_id = ?
        ''', (job_id,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all skills with job counts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.skill_name, COUNT(js.job_id) as job_count
            FROM skills s
            LEFT JOIN job_skills js ON s.id = js.skill_id
            GROUP BY s.skill_name
            ORDER BY job_count DESC
        ''')
        
        return [{'skill': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT company) FROM jobs')
        total_companies = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT location) FROM jobs')
        total_locations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM skills')
        total_skills = cursor.fetchone()[0]
        
        cursor.execute('SELECT source, COUNT(*) as count FROM jobs GROUP BY source')
        jobs_by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_jobs': total_jobs,
            'total_companies': total_companies,
            'total_locations': total_locations,
            'total_skills': total_skills,
            'jobs_by_source': jobs_by_source
        }
    
    def export_to_json(self, filename: str, filters: Optional[Dict] = None):
        """Export jobs to JSON file"""
        jobs = self.filter_jobs(**(filters or {}))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False, default=str)
    
    def close(self):
        """Close thread-local database connection"""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None

# Global instance
job_db = JobDatabase()

def store_jobs_in_db(jobs: List[Dict[str, Any]]) -> int:
    """
    Convenience function to store jobs (compatible with original API)
    """
    return job_db.store_jobs(jobs)

if __name__ == "__main__":
    # Example usage
    db = JobDatabase()
    
    # Example jobs
    sample_jobs = [
        {
            'title': 'Python Developer',
            'company': 'Tech Corp',
            'location': 'Johannesburg, SA',
            'description': 'Looking for Python developer with Django and Flask experience',
            'url': 'https://example.com/job1',
            'source': 'indeed',
            'skills': ['Python', 'Django', 'Flask']
        },
        {
            'title': 'Data Scientist',
            'company': 'Data Inc',
            'location': 'Cape Town, SA',
            'description': 'Data scientist needed with Python, ML, and TensorFlow skills',
            'url': 'https://example.com/job2',
            'source': 'linkedin',
            'skills': ['Python', 'Machine Learning', 'TensorFlow']
        }
    ]
    
    # Store jobs
    count = db.store_jobs(sample_jobs)
    print(f"Stored {count} jobs")
    
    # Search jobs
    results = db.search_jobs('python developer')
    print(f"\nFound {len(results)} jobs for 'python developer'")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\nDatabase stats: {stats}")
    
    db.close()
