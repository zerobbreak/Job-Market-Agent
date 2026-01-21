import logging
import os
import time
import numpy as np
import re
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import google.genai as genai
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MatchScore:
    total_score: float  # 0 to 100
    semantic_score: float
    keyword_score: float
    explanation: List[str]
    breakdown: Dict[str, float]

class SemanticMatcher:
    """
    Battle-Tested Matching Service using Hybrid Retrieval (Vector + BM25-like + Rules).
    Uses Google Gemini Embeddings for semantic understanding, combined with explicit rule-based scoring.
    """

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.client = None
        self._setup_client()
        # Rate Limiting: 10 requests per minute
        self.last_request_time = 0
        self.request_interval = 6.0  # seconds between requests

        # Weights Configuration (Optimized for AI/Semantic preference)
        self.weights = {
            'skills': 0.20,      # Reduced from 0.35 (too brittle)
            'title': 0.15,       # Reduced from 0.20
            'experience': 0.15,  # Unchanged
            'semantic': 0.40,    # Increased from 0.15 (Primary driver)
            'location': 0.10,    # Unchanged
            'salary': 0.00       # Removed (often missing)
        }

    def _wait_for_rate_limit(self):
        """Simple rate limiting to prevent API abuse"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _setup_client(self):
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to init Gemini for embeddings: {e}")

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get vector embedding from Gemini with rate limiting"""
        if not self.client or not text:
            return None
        
        self._wait_for_rate_limit()
        
        try:
            # text-embedding-004 is optimized for retrieval/similarity
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return np.array(response.embeddings[0].values)
        except Exception as e:
            logger.warning(f"Embedding API error: {e}")
            return None

    def calculate_match(self, profile: Dict[str, Any], job: Dict[str, Any]) -> MatchScore:
        """
        Calculate comprehensive match score using Hybrid Search.
        """
        reasons = []
        breakdown = {}

        # 1. Semantic Score (Embeddings)
        semantic_score = 0.0
        try:
            profile_text = self._profile_to_text(profile)
            job_text = self._job_to_text(job)
            
            profile_vec = self.get_embedding(profile_text)
            job_vec = self.get_embedding(job_text)
            
            if profile_vec is not None and job_vec is not None:
                similarity = np.dot(profile_vec, job_vec) / (np.linalg.norm(profile_vec) * np.linalg.norm(job_vec))
                semantic_score = max(0.0, float(similarity) * 100)
                
                # Boost strong matches to separate from noise (Calibration)
                if semantic_score > 70:
                    semantic_score = min(100, semantic_score + 15) # 74 -> 89
                elif semantic_score < 50:
                    semantic_score = max(0, semantic_score - 10) # 41 -> 31
                
                if semantic_score > 75:
                    reasons.append("Strong semantic match with job description.")
        except Exception as e:
            logger.warning(f"Semantic match failed: {e}")
        
        breakdown['semantic'] = semantic_score

        # 2. Skills Match (Keyword Overlap)
        skills_score = self._calculate_skills_score(profile, job)
        breakdown['skills'] = skills_score
        if skills_score > 80:
            reasons.append("High overlap of required skills.")

        # 3. Title Similarity (Simple Token Overlap)
        title_score = self._calculate_title_score(profile, job)
        breakdown['title'] = title_score
        if title_score > 80:
            reasons.append("Job title aligns well with your profile.")

        # 4. Experience Fit
        exp_score = self._calculate_experience_score(profile, job)
        breakdown['experience'] = exp_score

        # 5. Location Fit
        loc_score = self._calculate_location_score(profile, job)
        breakdown['location'] = loc_score
        if loc_score == 100:
            reasons.append("Location matches perfectly.")

        # 6. Salary Fit (Placeholder - hard to parse typically)
        salary_score = 50.0 # Neutral default
        breakdown['salary'] = salary_score

        # 7. Weighted Total
        total_score = (
            (skills_score * self.weights['skills']) +
            (title_score * self.weights['title']) +
            (exp_score * self.weights['experience']) +
            (semantic_score * self.weights['semantic']) +
            (loc_score * self.weights['location']) +
            (salary_score * self.weights['salary'])
        )

        # Normalize logic: if semantic is 0 (API fail), re-distribute semantic weight to skills/title
        if semantic_score == 0:
            total_score = (
                (skills_score * 0.5) +
                (title_score * 0.25) +
                (exp_score * 0.15) +
                (loc_score * 0.10)
            )

        # Hard Rules / Penalties
        # Example: Seniority mismatch penalty
        job_title_lower = job.get('title', '').lower()
        profile_exp_lower = str(profile.get('experience_level', '')).lower()
        if 'senior' in job_title_lower and ('junior' in profile_exp_lower or 'entry' in profile_exp_lower):
            total_score *= 0.8 # 20% penalty
            reasons.append("Warning: Job may be too senior for current level.")

        return MatchScore(
            total_score=round(min(100, total_score), 1),
            semantic_score=round(semantic_score, 1),
            keyword_score=round(skills_score, 1), # Mapping skills to keyword for backward compat
            explanation=reasons,
            breakdown=breakdown
        )

    def _profile_to_text(self, profile: Dict[str, Any]) -> str:
        """Convert structured profile to rich text for embedding"""
        skills = ", ".join(profile.get('skills', []))
        experience = profile.get('experience_level', '')
        goals = profile.get('career_goals', '')
        summary = profile.get('summary', '') # Assuming summary might exist
        return f"Role: {experience} Developer. Skills: {skills}. Goals: {goals}. Summary: {summary}."

    def _job_to_text(self, job: Dict[str, Any]) -> str:
        return f"{job.get('title', '')}. {job.get('description', '')}. {job.get('company', '')}"

    def _calculate_skills_score(self, profile: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Jaccard-like similarity on skills"""
        profile_skills = set(s.lower() for s in profile.get('skills', []))
        if not profile_skills:
            return 0.0
        
        job_text = (job.get('description', '') + ' ' + job.get('title', '')).lower()
        # Simple extraction: check if skill appears in job text
        found = sum(1 for skill in profile_skills if skill in job_text)
        
        # Cap denominator to avoid penalizing "too many skills"
        effective_total = min(len(profile_skills), 10) 
        if effective_total == 0: return 0.0
        
        return min((found / effective_total) * 100, 100)

    def _calculate_title_score(self, profile: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Token overlap between career goals/current role and job title"""
        job_title = job.get('title', '').lower()
        # Use career goals or construct a "current title" from experience + top skill
        goals = profile.get('career_goals', '').lower()
        
        # Normalize synonyms
        synonyms = {
            'engineer': 'developer',
            'programmer': 'developer',
            'coder': 'developer',
            'architect': 'developer',
            'back-end': 'backend',
            'front-end': 'frontend',
            'js': 'javascript',
            'ts': 'typescript'
        }
        
        for k, v in synonyms.items():
            job_title = job_title.replace(k, v)
            goals = goals.replace(k, v)
        
        if not goals:
            # Fallback
            top_skill = (profile.get('skills', []) + [''])[0].lower()
            exp = str(profile.get('experience_level', '')).lower()
            goals = f"{exp} {top_skill} developer"

        # Tokenize
        job_tokens = set(re.findall(r'\w+', job_title))
        profile_tokens = set(re.findall(r'\w+', goals))
        
        if not job_tokens or not profile_tokens:
            return 0.0
            
        intersection = job_tokens.intersection(profile_tokens)
        # Jaccard
        return (len(intersection) / len(job_tokens.union(profile_tokens))) * 100

    def _calculate_experience_score(self, profile: Dict[str, Any], job: Dict[str, Any]) -> float:
        """Heuristic experience matching"""
        # Map strings to approx years
        levels = {'intern': 0, 'junior': 1, 'entry': 1, 'mid': 3, 'senior': 5, 'lead': 7, 'principal': 10}
        
        p_level = str(profile.get('experience_level', '')).lower()
        j_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        
        p_years = 2 # default mid
        for k, v in levels.items():
            if k in p_level:
                p_years = v
                break
                
        j_years = 0 # default
        for k, v in levels.items():
            if k in j_text:
                j_years = v
                # Take the highest requirement found? Or first?
                # Usually job titles have the seniority.
                if k in job.get('title', '').lower():
                    j_years = v
                    break
        
        # If job has no explicit level, assume it matches nicely (score 80)
        if j_years == 0:
            return 80.0
            
        diff = abs(p_years - j_years)
        if diff == 0: return 100.0
        if diff <= 2: return 80.0
        if diff <= 4: return 50.0
        return 20.0

    def _calculate_location_score(self, profile: Dict[str, Any], job: Dict[str, Any]) -> float:
        p_loc = profile.get('location', '').lower()
        j_loc = job.get('location', '').lower()
        j_desc = job.get('description', '').lower()
        
        if 'remote' in j_loc or 'remote' in j_desc:
            return 100.0
            
        if not p_loc or not j_loc:
            return 50.0 # Neutral
            
        if p_loc in j_loc or j_loc in p_loc:
            return 100.0
            
        return 0.0 # Different location and not remote
