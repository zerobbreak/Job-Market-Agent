
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Import the new semantic matcher (Gemini-based)
try:
    from .semantic_matching import SemanticJobMatcher
    SEMANTIC_MATCHER_AVAILABLE = True
except ImportError:
    SEMANTIC_MATCHER_AVAILABLE = False
    logger.warning("Semantic matcher not available. Using TF-IDF only.")

class AdvancedJobMatcher:
    def __init__(self, use_embeddings: bool = False):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.use_embeddings = use_embeddings
        
        # Use semantic matcher (Gemini) if available
        if SEMANTIC_MATCHER_AVAILABLE and use_embeddings:
            try:
                self.semantic_matcher = SemanticJobMatcher(use_embeddings=True)
                self.use_semantic = True
            except Exception as e:
                logger.warning(f"Failed to initialize semantic matcher: {e}. Using TF-IDF.")
                self.use_semantic = False
        else:
            self.use_semantic = False

    def _prepare_text(self, text: str) -> str:
        if not text:
            return ""
        return str(text).lower()

    def match_jobs(self, profile: Dict[str, Any], jobs: List[Dict[str, Any]], min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Match jobs to profile using semantic embeddings (if available) or TF-IDF.
        
        Args:
            profile: User profile dictionary
            jobs: List of job dictionaries
            min_score: Minimum match score to include (0-100)
        """
        if not jobs:
            return []
        
        # Use semantic matcher if available
        if self.use_semantic and hasattr(self, 'semantic_matcher'):
            try:
                return self.semantic_matcher.match_jobs(profile, jobs, min_score)
            except Exception as e:
                logger.error(f"Semantic matching failed: {e}. Falling back to TF-IDF.")
                # Fall through to TF-IDF
        
        # Fallback to TF-IDF matching

        # 1. Prepare Profile Text
        # Combine skills, experience, and bio into one rich text block
        skills = " ".join(profile.get('skills', []))
        experience = profile.get('experience_level', '')
        bio = profile.get('career_goals', '') or profile.get('professional_profile', '')
        education = profile.get('education', '')
        
        profile_text = f"{skills} {experience} {bio} {education}"
        profile_text = self._prepare_text(profile_text)

        # 2. Prepare Job Texts
        job_texts = []
        for job in jobs:
            title = job.get('title', '')
            desc = job.get('description', '')
            company = job.get('company', '')
            # Weight the title heavily by repeating it
            job_text = f"{title} {title} {title} {company} {desc}"
            job_texts.append(self._prepare_text(job_text))

        # 3. Vectorize
        try:
            all_texts = [profile_text] + job_texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # 4. Compute Similarity
            # Profile is at index 0, jobs are at 1..N
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # 5. Attach scores
            matched_jobs = []
            for i, score in enumerate(cosine_sim):
                job = jobs[i].copy()
                # Normalize score to 0-100
                final_score = round(score * 100)
                
                # Boost score if location matches (simple heuristic)
                if profile.get('location') and job.get('location'):
                    if profile['location'].lower() in job['location'].lower():
                        final_score += 10
                
                final_score = min(final_score, 100)
                
                # Generate reasons
                reasons = []
                if final_score > 70:
                    reasons.append("High semantic match with your profile")
                elif final_score > 50:
                    reasons.append("Good overlap with your skills")
                
                # Add specific skill matches
                job_desc_lower = job.get('description', '').lower()
                matched_skills = [s for s in profile.get('skills', []) if s.lower() in job_desc_lower]
                if matched_skills:
                    reasons.append(f"Matches skills: {', '.join(matched_skills[:3])}")

                job['match_score'] = final_score
                job['match_reasons'] = reasons
                matched_jobs.append(job)
                
            # Sort by score
            matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            return matched_jobs

        except Exception as e:
            logger.error(f"Error in ML matching: {e}")
            # Fallback to returning original jobs with 0 score
            for job in jobs:
                job['match_score'] = 0
                job['match_reasons'] = ["Matching failed"]
            return jobs


# Global matcher instance (singleton pattern)
_matcher_instance = None

def get_matcher(use_embeddings: bool = True) -> AdvancedJobMatcher:
    """Get or create a global matcher instance.

    Uses Gemini embeddings when GEMINI_API_KEY/GOOGLE_API_KEY is set,
    otherwise falls back to TF-IDF.
    """
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = AdvancedJobMatcher(use_embeddings=use_embeddings)
    return _matcher_instance


def match_student_to_jobs_ml(student_profile: Dict[str, Any], jobs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Match student profile to jobs using ML (semantic or TF-IDF).
    
    Args:
        student_profile: Student profile dictionary
        jobs: Optional list of jobs. If None, returns empty list.
    
    Returns:
        List of matched jobs with scores
    """
    if jobs is None:
        return []
    
    # Use semantic matching when Gemini key is available
    use_embeddings = bool(os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
    matcher = get_matcher(use_embeddings=use_embeddings)
    return matcher.match_jobs(student_profile, jobs, min_score=0.0)
