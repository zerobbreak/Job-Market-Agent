"""
Modern Recommendation Engine for Job Matching.
Implements Retrieval-Augmented Generation (RAG) style matching:
1. Retrieval: Fast Vector Search (Gemini Embeddings + Caching)
2. Ranking: Detailed Business Logic (Skills, Experience, Location)
"""

import os
import json
import logging
import time
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from utils.scraping import get_gemini_client

logger = logging.getLogger(__name__)

# Constants
CACHE_DIR = Path("data/cache")
EMBEDDING_CACHE_FILE = CACHE_DIR / "job_embeddings.json"
MODEL_NAME = "text-embedding-004"

@dataclass
class MatchResult:
    job_id: str
    job_data: Dict[str, Any]
    total_score: float
    semantic_score: float
    skills_score: float
    experience_score: float
    location_score: float
    reasons: List[str]

class JobVectorStore:
    """
    Handles vector embedding generation, storage, and retrieval.
    Acts as an in-memory vector database with disk persistence.
    """
    
    def __init__(self):
        self.embeddings: Dict[str, List[float]] = {}
        self.job_map: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        
    def _load_cache(self):
        """Load embeddings from disk cache."""
        if EMBEDDING_CACHE_FILE.exists():
            try:
                with open(EMBEDDING_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.embeddings = data.get("embeddings", {})
                    # We don't cache job data itself here, assuming it comes from DB
                    logger.info(f"Loaded {len(self.embeddings)} embeddings from cache.")
            except Exception as e:
                logger.error(f"Failed to load embedding cache: {e}")
                self.embeddings = {}
        else:
            # Ensure directory exists
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _save_cache(self):
        """Save embeddings to disk cache."""
        try:
            with open(EMBEDDING_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump({"embeddings": self.embeddings, "updated_at": str(datetime.now())}, f)
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Gemini API."""
        client = get_gemini_client()
        if not client:
            logger.error("Gemini client not available.")
            return None
            
        try:
            # Rate limit handling could be added here
            response = client.models.embed_content(
                model=MODEL_NAME,
                contents=text[:9000] # Safety truncate
            )
            
            # Handle different response structures
            if hasattr(response, "embeddings") and response.embeddings:
                emb = response.embeddings[0]
                values = getattr(emb, "values", None) or getattr(emb, "values_", None)
                if values:
                    return list(values)
            
            return None
        except Exception as e:
            logger.error(f"Embedding API error: {e}")
            return None

    def _job_to_text(self, job: Dict[str, Any]) -> str:
        """Convert job to rich text for embedding."""
        return f"{job.get('title', '')}. {job.get('company', '')}. {job.get('description', '')}. {job.get('location', '')}"

    def update_index(self, jobs: List[Dict[str, Any]]):
        """Update the vector index with new jobs."""
        updates = 0
        for job in jobs:
            # Use job URL or ID as unique key
            job_id = job.get('id') or job.get('url') or job.get('job_url')
            if not job_id:
                continue
                
            self.job_map[job_id] = job
            
            # Check if we already have an embedding
            if job_id not in self.embeddings:
                text = self._job_to_text(job)
                vec = self._get_embedding(text)
                if vec:
                    self.embeddings[job_id] = vec
                    updates += 1
                    time.sleep(0.5) # Basic rate limiting
        
        if updates > 0:
            self._save_cache()
            logger.info(f"Updated index with {updates} new embeddings.")

    def search(self, query_text: str, k: int = 50, filter_ids: List[str] = None) -> List[Tuple[str, float]]:
        """
        Semantic search for top K jobs.
        Returns list of (job_id, similarity_score).
        """
        query_vec = self._get_embedding(query_text)
        if not query_vec:
            return []
            
        query_arr = np.array(query_vec)
        results = []
        
        # In a real production system, use FAISS or Annoy here.
        # For <10k jobs, numpy dot product is plenty fast.
        
        # Convert dictionary to matrix for speed
        ids = list(self.embeddings.keys())
        
        # Apply filter if provided
        if filter_ids:
            # Only keep IDs that are in the filter list AND in embeddings
            ids = [pid for pid in ids if pid in filter_ids]
            
        if not ids:
            return []
            
        vectors = np.array([self.embeddings[id] for id in ids])
        
        # Cosine Similarity: (A . B) / (|A| * |B|)
        # Assuming embeddings are not normalized, we compute full cosine
        norm_v = np.linalg.norm(vectors, axis=1)
        norm_q = np.linalg.norm(query_arr)
        
        if norm_q == 0:
            return []
            
        # Avoid division by zero
        norm_v[norm_v == 0] = 1e-10
        
        scores = np.dot(vectors, query_arr) / (norm_v * norm_q)
        
        # Zip and sort
        id_scores = list(zip(ids, scores))
        id_scores.sort(key=lambda x: x[1], reverse=True)
        
        return id_scores[:k]

class RecommendationEngine:
    """
    Main service for job matching.
    Orchestrates Retrieval (VectorStore) and Ranking (Business Logic).
    """
    
    def __init__(self):
        self.vector_store = JobVectorStore()
        
    def _profile_to_text(self, profile: Dict[str, Any]) -> str:
        """Convert profile to query text."""
        skills = ", ".join(profile.get('skills', []))
        exp = profile.get('experience_level', '')
        goals = profile.get('career_goals', '')
        return f"I am a {exp} developer with skills in {skills}. Looking for: {goals}."

    def _calculate_skills_score(self, profile_skills: List[str], job_text: str) -> Tuple[float, List[str]]:
        """
        Robust skills matching.
        Returns (score 0-100, list of matched skills).
        """
        if not profile_skills:
            return 0.0, []
            
        job_text_lower = job_text.lower()
        matched = []
        
        # Normalize and check
        # TODO: Add a synonym dictionary (e.g. JS -> JavaScript)
        for skill in profile_skills:
            s_lower = skill.lower()
            # Simple boundary check to avoid "Java" matching "JavaScript"
            # Regex: word boundary or start/end of string
            # Escaping skill name for regex safety
            try:
                pattern = r'(^|[\s\.,;:\(\)])' + re.escape(s_lower) + r'($|[\s\.,;:\(\)])'
                if re.search(pattern, job_text_lower):
                    matched.append(skill)
            except:
                # Fallback to simple inclusion if regex fails
                if s_lower in job_text_lower:
                    matched.append(skill)
                    
        if not matched:
            return 0.0, []
            
        # Jaccard-ish: Matched / Total Profile Skills
        # We focus on recall (how many of MY skills are needed?)
        score = (len(matched) / len(profile_skills)) * 100
        return min(100.0, score), matched

    def _calculate_experience_score(self, profile_level: str, job_text: str) -> float:
        """
        Extracts years from job description and compares.
        """
        job_text_lower = job_text.lower()
        profile_level = str(profile_level).lower()
        
        # Map profile to years
        p_years = 2 # Default Mid
        if 'intern' in profile_level: p_years = 0
        elif 'junior' in profile_level or 'entry' in profile_level: p_years = 1
        elif 'mid' in profile_level: p_years = 3
        elif 'senior' in profile_level: p_years = 5
        elif 'lead' in profile_level or 'principal' in profile_level: p_years = 8
        elif 'manager' in profile_level: p_years = 7
        
        # Extract years from job
        # Regex for "X+ years", "X-Y years"
        years_req = 0
        matches = re.findall(r'(\d+)[\+]?\s*-?\s*(\d+)?\s*years?', job_text_lower)
        if matches:
            # Take the max year mentioned generally, or min? 
            # Usually "3+ years" -> 3. "3-5 years" -> 3.
            try:
                years_req = int(matches[0][0])
            except:
                pass
        else:
            # Fallback to keywords
            if 'senior' in job_text_lower: years_req = 5
            elif 'lead' in job_text_lower: years_req = 7
            elif 'junior' in job_text_lower: years_req = 1
            
        # Scoring
        if p_years >= years_req:
            return 100.0
        elif p_years >= years_req - 1:
            return 80.0 # Slightly under
        elif p_years >= years_req - 2:
            return 50.0 # Reach
        else:
            return 20.0 # Too senior

    def match_jobs(self, profile: Dict[str, Any], jobs: List[Dict[str, Any]], fresh_only: bool = False) -> List[Dict[str, Any]]:
        """
        Main entry point.
        1. Updates index with provided jobs (if new).
        2. Retrieves top candidates via Semantics.
        3. Ranks candidates via Business Logic.
        
        Args:
            profile: User profile data
            jobs: List of jobs to match against
            fresh_only: If True, only matches against the provided 'jobs' list (ignoring older cached jobs)
        """
        if not jobs:
            return []
            
        # 1. Update Index
        self.vector_store.update_index(jobs)
        
        # 2. Retrieval (Semantic Search)
        query = self._profile_to_text(profile)
        
        # Prepare filter if fresh_only is requested
        filter_ids = None
        if fresh_only:
            filter_ids = [j.get('id') or j.get('url') or j.get('job_url') for j in jobs]
            # Remove Nones
            filter_ids = [fid for fid in filter_ids if fid]
        
        # Retrieve
        # If fresh_only, we want to rank ALL the fresh jobs, so k should be at least len(jobs)
        k = len(jobs) if fresh_only else min(len(jobs), 50)
        candidates = self.vector_store.search(query, k=k, filter_ids=filter_ids)
        
        results = []
        
        # 3. Ranking
        profile_skills = profile.get('skills', [])
        profile_exp = profile.get('experience_level', '')
        profile_loc = profile.get('location', '').lower()
        
        for job_id, semantic_score in candidates:
            job = self.vector_store.job_map.get(job_id)
            if not job: 
                # Fallback if job was passed in but not in map yet (edge case)
                job = next((j for j in jobs if (j.get('id') or j.get('url')) == job_id), None)
            
            if not job: continue
            
            job_text = f"{job.get('title', '')} {job.get('description', '')}"
            
            # -- Business Logic Scoring --
            
            # Skills (30%)
            skills_score, matched_skills = self._calculate_skills_score(profile_skills, job_text)
            
            # Experience (15%)
            exp_score = self._calculate_experience_score(profile_exp, job_text)
            
            # Location (15%) - Strict Filter Logic implemented as score
            loc_score = 0.0
            job_loc = job.get('location', '').lower()
            if 'remote' in job_loc or 'remote' in job_text.lower():
                loc_score = 100.0
            elif profile_loc and (profile_loc in job_loc or job_loc in profile_loc):
                loc_score = 100.0
            elif not profile_loc:
                loc_score = 50.0 # Neutral
            else:
                loc_score = 0.0
                
            # Role Fit (10%) - Based on Career Goals / Suggested Roles
            role_score = 0.0
            profile_goals = str(profile.get('career_goals', '')).lower()
            j_title = job.get('title', '').lower()
            
            if profile_goals and j_title:
                # Direct match
                if j_title in profile_goals or profile_goals in j_title:
                    role_score = 100.0
                else:
                    # Check individual suggested roles
                    # Assuming they might be comma separated in career_goals
                    roles = [r.strip() for r in profile_goals.replace('suggested:', '').split(',')]
                    for role in roles:
                        if role and (role in j_title or j_title in role):
                            role_score = 100.0
                            break
                    
                    # Partial match if no direct match
                    if role_score == 0:
                        common = set(j_title.split()) & set(profile_goals.split())
                        # Filter out common stop words like "developer", "engineer" to avoid false positives?
                        # Actually "developer" is a good match if both have it.
                        if len(common) >= 2: # At least 2 words match (e.g. "Python Developer")
                            role_score = 60.0
                        elif len(common) == 1:
                            role_score = 30.0

            # Semantic (35%) - Normalized to 0-100
            sem_score_100 = max(0.0, semantic_score * 100)
            
            # Weighted Total
            # Weights: Sem: 35, Skill: 25, Exp: 15, Loc: 15, Role: 10
            total = (sem_score_100 * 0.35) + (skills_score * 0.25) + (exp_score * 0.15) + (loc_score * 0.15) + (role_score * 0.10)
            
            # Penalties
            if loc_score == 0:
                total *= 0.5 # Heavy penalty for wrong location (if not remote)
            
            # Reasons
            reasons = []
            if sem_score_100 > 80: reasons.append("Strong semantic match")
            if len(matched_skills) > 0: reasons.append(f"Matches skills: {', '.join(matched_skills[:3])}")
            if exp_score == 100: reasons.append("Experience level fits well")
            if loc_score == 100: reasons.append("Location alignment")
            if role_score > 80: reasons.append("Role title aligns with goals")
            
            # Construct Result
            matched_job = job.copy()
            matched_job['match_score'] = round(total, 1)
            matched_job['match_reasons'] = reasons
            matched_job['score_breakdown'] = {
                'semantic': round(sem_score_100, 1),
                'skills': round(skills_score, 1),
                'experience': round(exp_score, 1),
                'location': round(loc_score, 1),
                'role_fit': round(role_score, 1)
            }
            
            results.append(matched_job)
            
        # Sort by final score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results

    def get_market_stats(self, role: str = None, location: str = None) -> Dict[str, Any]:
        """
        Calculate market statistics based on the job vector store.
        """
        jobs = list(self.vector_store.job_map.values())
        if not jobs:
            return {"error": "No data available"}
            
        filtered_jobs = []
        for job in jobs:
            # Fuzzy match role/location if provided
            j_title = job.get('title', '').lower()
            j_loc = job.get('location', '').lower()
            j_desc = job.get('description', '').lower()
            
            if role and role.lower() not in j_title and role.lower() not in j_desc:
                continue
            if location and location.lower() not in j_loc:
                continue
                
            filtered_jobs.append(job)
            
        if not filtered_jobs:
            return {"count": 0, "message": "No jobs found for this criteria"}
            
        # Extract Salaries
        salaries = []
        for job in filtered_jobs:
            text = (job.get('description', '') + " " + job.get('salary', '')).lower()
            # Regex for South African Rands (Annual or Monthly)
            # R10,000 - R20,000
            # R 300k
            matches = re.findall(r'r\s?(\d{2,3}[,\.]?\d{3})', text)
            for m in matches:
                try:
                    val = float(m.replace(',', '').replace('.', ''))
                    # Filter outliers (likely monthly if < 100k, annual if > 100k)
                    # Normalize to Annual
                    if 5000 < val < 100000: # Monthly likely
                        salaries.append(val * 12)
                    elif val >= 100000: # Annual likely
                        salaries.append(val)
                except:
                    pass
                    
        # Extract Top Skills
        skill_counts = {}
        common_skills = ['python', 'java', 'javascript', 'react', 'sql', 'aws', 'docker', 'typescript', 'c#', '.net', 'html', 'css', 'git', 'agile', 'linux', 'excel', 'communication', 'leadership']
        
        for job in filtered_jobs:
            desc = job.get('description', '').lower()
            for skill in common_skills:
                if skill in desc:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                    
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Stats
        avg_salary = sum(salaries) / len(salaries) if salaries else 0
        min_salary = min(salaries) if salaries else 0
        max_salary = max(salaries) if salaries else 0
        
        return {
            "count": len(filtered_jobs),
            "avg_salary": round(avg_salary, 2),
            "salary_range": {"min": min_salary, "max": max_salary},
            "top_skills": [{"name": k, "count": v} for k, v in sorted_skills],
            "sample_size_salaries": len(salaries)
        }

# Singleton instance
engine = RecommendationEngine()
