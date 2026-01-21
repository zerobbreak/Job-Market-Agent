"""
AI-Driven Semantic Job Matching Engine
Implements battle-tested solution: Semantic embeddings with vector similarity search
Based on industry leaders: LinkedIn, ZipRecruiter, Indeed
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
import os
from functools import lru_cache
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

from utils.scraping import get_gemini_client

logger = logging.getLogger(__name__)


class SemanticJobMatcher:
    """
    Battle-tested AI-driven semantic matching engine.
    
    Features:
    - Semantic embeddings for deep understanding (like LinkedIn)
    - Multi-dimensional scoring (skills, experience, goals, location)
    - Personalized ranking based on profile completeness
    - Vector similarity search for accurate matching
    """
    
    def __init__(self, use_embeddings: bool = True, model: str = "text-embedding-004"):
        """
        Initialize the semantic matcher.
        
        Args:
            use_embeddings: Whether to use Gemini embeddings (requires API key)
            model: Gemini embedding model to use (e.g. "text-embedding-004")
        """
        # Decide if we can use embeddings based on Gemini client availability
        self.use_embeddings = use_embeddings and get_gemini_client() is not None
        self.model = model
        self.embedding_cache = {}
        
        # Fallback TF-IDF vectorizer
        if not self.use_embeddings:
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,
                ngram_range=(1, 2)
            )
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using Gemini embeddings API."""
        if not self.use_embeddings:
            return None
        
        client = get_gemini_client()
        if client is None:
            return None
        
        # Check cache
        cache_key = hash(text[:500])  # Cache key from first 500 chars
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            # Truncate very long texts (token/size limits safety)
            text_truncated = text[:8000] if len(text) > 8000 else text
            
            # Gemini embeddings API
            response = client.models.embed_content(
                model=self.model,
                contents=text_truncated,
            )
            # google-genai returns embeddings list with .values
            embedding_values = None
            if hasattr(response, "embeddings") and response.embeddings:
                emb = response.embeddings[0]
                embedding_values = getattr(emb, "values", None) or getattr(emb, "values_", None)
            
            if not embedding_values:
                raise ValueError("Empty embedding response from Gemini")
            
            embedding = np.array(embedding_values, dtype=float)
            
            # Cache the result
            self.embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error getting Gemini embedding: {e}")
            return None
    
    def _prepare_profile_text(self, profile: Dict[str, Any]) -> str:
        """Prepare comprehensive profile text for embedding."""
        parts = []
        
        # Skills (weighted heavily)
        skills = profile.get('skills', [])
        if skills:
            parts.append("Skills: " + ", ".join(skills))
            parts.append(" ".join(skills) * 2)  # Repeat for emphasis
        
        # Experience level
        exp_level = profile.get('experience_level', '')
        if exp_level:
            parts.append(f"Experience: {exp_level}")
        
        # Career goals (important for semantic matching)
        career_goals = profile.get('career_goals', '') or profile.get('professional_profile', '')
        if career_goals:
            parts.append(f"Career goals: {career_goals}")
        
        # Education
        education = profile.get('education', '')
        if education:
            parts.append(f"Education: {education}")
        
        # Strengths
        strengths = profile.get('strengths', [])
        if strengths:
            parts.append("Strengths: " + ", ".join(strengths))
        
        return " ".join(parts)
    
    def _prepare_job_text(self, job: Dict[str, Any]) -> str:
        """Prepare comprehensive job text for embedding."""
        parts = []
        
        # Title (weighted heavily - repeat 3x)
        title = job.get('title', '')
        if title:
            parts.append(title)
            parts.append(title)
            parts.append(title)
        
        # Description
        desc = job.get('description', '')
        if desc:
            parts.append(desc)
        
        # Company
        company = job.get('company', '')
        if company:
            parts.append(f"Company: {company}")
        
        # Location
        location = job.get('location', '')
        if location:
            parts.append(f"Location: {location}")
        
        return " ".join(parts)
    
    def _compute_semantic_similarity(self, profile_text: str, job_texts: List[str]) -> np.ndarray:
        """
        Compute semantic similarity between profile and jobs.
        Returns array of similarity scores.
        """
        if self.use_embeddings:
            # Use OpenAI embeddings
            profile_embedding = self._get_embedding(profile_text)
            if profile_embedding is None:
                # Fallback to TF-IDF
                return self._compute_tfidf_similarity(profile_text, job_texts)
            
            job_embeddings = []
            for job_text in job_texts:
                embedding = self._get_embedding(job_text)
                if embedding is None:
                    # Fallback to TF-IDF for this job
                    return self._compute_tfidf_similarity(profile_text, job_texts)
                job_embeddings.append(embedding)
            
            # Compute cosine similarity
            job_embeddings_matrix = np.array(job_embeddings)
            similarities = np.dot(job_embeddings_matrix, profile_embedding) / (
                np.linalg.norm(job_embeddings_matrix, axis=1) * np.linalg.norm(profile_embedding)
            )
            return similarities
        else:
            # Use TF-IDF fallback
            return self._compute_tfidf_similarity(profile_text, job_texts)
    
    def _compute_tfidf_similarity(self, profile_text: str, job_texts: List[str]) -> np.ndarray:
        """Fallback TF-IDF similarity computation."""
        try:
            all_texts = [profile_text] + job_texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            similarities = sklearn_cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            return similarities
        except Exception as e:
            logger.error(f"Error in TF-IDF similarity: {e}")
            return np.zeros(len(job_texts))
    
    def _compute_multi_dimensional_score(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        semantic_score: float
    ) -> Dict[str, Any]:
        """
        Compute multi-dimensional match score (battle-tested approach).
        
        Dimensions:
        1. Semantic Match (40%) - Deep understanding of fit
        2. Skills Match (25%) - Technical/professional skills
        3. Experience Match (15%) - Level alignment
        4. Location Match (10%) - Geographic feasibility
        5. Career Goals Match (10%) - Aspiration alignment
        """
        score_breakdown = {
            'semantic': 0,
            'skills': 0,
            'experience': 0,
            'location': 0,
            'career_goals': 0
        }
        
        # 1. Semantic Match (40%)
        score_breakdown['semantic'] = semantic_score * 40
        
        # 2. Skills Match (25%)
        profile_skills = [s.lower() for s in profile.get('skills', [])]
        job_text = (
            job.get('title', '') + ' ' + 
            job.get('description', '') + ' ' +
            job.get('company', '')
        ).lower()
        
        matched_skills = [s for s in profile_skills if s in job_text]
        if profile_skills:
            skills_ratio = len(matched_skills) / len(profile_skills)
            score_breakdown['skills'] = min(skills_ratio * 25, 25)
        else:
            score_breakdown['skills'] = 0
        
        # 3. Experience Match (15%)
        profile_exp = profile.get('experience_level', '').lower()
        job_text_lower = job_text.lower()
        
        exp_match = False
        if 'senior' in profile_exp and ('senior' in job_text_lower or 'lead' in job_text_lower):
            exp_match = True
        elif 'mid' in profile_exp or 'intermediate' in profile_exp:
            if 'mid' in job_text_lower or 'intermediate' in job_text_lower or 'junior' in job_text_lower:
                exp_match = True
        elif 'junior' in profile_exp or 'entry' in profile_exp:
            if 'junior' in job_text_lower or 'entry' in job_text_lower or 'graduate' in job_text_lower:
                exp_match = True
        
        score_breakdown['experience'] = 15 if exp_match else 5
        
        # 4. Location Match (10%)
        profile_location = profile.get('location', '').lower()
        job_location = job.get('location', '').lower()
        
        if profile_location and job_location:
            # Check for city/country matches
            if profile_location in job_location or job_location in profile_location:
                score_breakdown['location'] = 10
            elif any(word in job_location for word in profile_location.split() if len(word) > 3):
                score_breakdown['location'] = 5
            else:
                score_breakdown['location'] = 0
        else:
            score_breakdown['location'] = 5  # Neutral if location not specified
        
        # 5. Career Goals Match (10%)
        career_goals = profile.get('career_goals', '').lower()
        if career_goals and job_text:
            # Simple keyword matching for career goals
            goal_keywords = set(career_goals.split())
            job_keywords = set(job_text.split())
            common_keywords = goal_keywords.intersection(job_keywords)
            if len(goal_keywords) > 0:
                goal_match_ratio = len(common_keywords) / len(goal_keywords)
                score_breakdown['career_goals'] = min(goal_match_ratio * 10, 10)
            else:
                score_breakdown['career_goals'] = 0
        else:
            score_breakdown['career_goals'] = 0
        
        # Calculate total score
        total_score = sum(score_breakdown.values())
        
        return {
            'total_score': round(total_score, 1),
            'breakdown': score_breakdown
        }
    
    def _generate_match_reasons(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        score_data: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []
        breakdown = score_data['breakdown']
        
        # Semantic match reason
        if breakdown['semantic'] > 30:
            reasons.append("Strong semantic alignment with your profile")
        elif breakdown['semantic'] > 20:
            reasons.append("Good semantic match with your background")
        
        # Skills match
        profile_skills = [s.lower() for s in profile.get('skills', [])]
        job_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        matched_skills = [s for s in profile_skills if s in job_text]
        
        if matched_skills:
            reasons.append(f"Matches {len(matched_skills)} of your skills: {', '.join(matched_skills[:3])}")
        
        # Experience match
        if breakdown['experience'] >= 15:
            reasons.append("Experience level aligns with your background")
        
        # Location match
        if breakdown['location'] >= 8:
            reasons.append("Location matches your preference")
        
        # Career goals
        if breakdown['career_goals'] >= 7:
            reasons.append("Aligns with your career goals")
        
        # Overall quality indicator
        if score_data['total_score'] >= 85:
            reasons.insert(0, "🌟 Exceptional match - highly recommended!")
        elif score_data['total_score'] >= 70:
            reasons.insert(0, "✨ Strong match - worth applying")
        elif score_data['total_score'] >= 55:
            reasons.insert(0, "✓ Good match - consider applying")
        
        return reasons[:5]  # Limit to top 5 reasons
    
    def match_jobs(
        self,
        profile: Dict[str, Any],
        jobs: List[Dict[str, Any]],
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Match jobs to profile using semantic similarity.
        
        Args:
            profile: User profile dictionary
            jobs: List of job dictionaries
            min_score: Minimum match score to include (0-100)
        
        Returns:
            List of matched jobs with scores and reasons, sorted by score
        """
        if not jobs:
            return []
        
        # Prepare texts
        profile_text = self._prepare_profile_text(profile)
        job_texts = [self._prepare_job_text(job) for job in jobs]
        
        # Compute semantic similarities
        semantic_scores = self._compute_semantic_similarity(profile_text, job_texts)
        
        # Compute multi-dimensional scores for each job
        matched_jobs = []
        for i, job in enumerate(jobs):
            semantic_score = float(semantic_scores[i])
            score_data = self._compute_multi_dimensional_score(profile, job, semantic_score)
            
            # Skip if below minimum score
            if score_data['total_score'] < min_score:
                continue
            
            # Create enhanced job match
            matched_job = job.copy()
            matched_job['match_score'] = score_data['total_score']
            matched_job['match_reasons'] = self._generate_match_reasons(profile, job, score_data)
            matched_job['score_breakdown'] = score_data['breakdown']
            matched_job['semantic_score'] = round(semantic_score * 100, 1)
            
            matched_jobs.append(matched_job)
        
        # Sort by total score (descending)
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched_jobs

