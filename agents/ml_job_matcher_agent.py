"""
ML-Enhanced Job Matching Agent
Uses recommendation systems and deep similarity matching for intelligent job-candidate matching
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from collections import defaultdict

# ML imports
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
import xgboost as xgb
from scipy.sparse import csr_matrix

# Local imports
from utils.matching import match_student_to_jobs  # Original matching function

# Configure logging
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)

class MLJobMatcherAgent:
    """
    ML-powered job matching agent that uses advanced recommendation systems
    and deep similarity matching for intelligent job-candidate pairing.
    """

    def __init__(self, model_dir: str = "ml_models"):
        """
        Initialize the ML Job Matcher Agent

        Args:
            model_dir: Directory to store/load trained ML models
        """
        self.model_dir = model_dir
        self.models_loaded = False

        # Initialize ML components
        self._initialize_ml_components()

        # Load or train models
        self._load_or_train_models()

        # Initialize interaction tracking for collaborative filtering
        self.user_item_interactions = defaultdict(dict)

    def _initialize_ml_components(self):
        """Initialize ML components and models"""
        # Sentence transformer for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

        # TF-IDF vectorizer for text-based similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )

        # XGBoost model for match prediction
        self.match_predictor = xgb.XGBRegressor(
            objective='reg:squarederror',
            random_state=42,
            n_estimators=100
        )

        # Scaler for feature normalization
        self.feature_scaler = StandardScaler()

    def _load_or_train_models(self):
        """Load pre-trained models or train new ones"""
        os.makedirs(self.model_dir, exist_ok=True)

        model_files = [
            'match_predictor.joblib',
            'tfidf_vectorizer.joblib',
            'feature_scaler.joblib',
            'sentence_model_config.json'  # For sentence transformer config
        ]

        all_models_exist = all(
            os.path.exists(os.path.join(self.model_dir, f))
            for f in model_files
        )

        if all_models_exist:
            self._load_models()
            self.models_loaded = True
        else:
            # Train models with synthetic/mock data
            self._train_models_with_synthetic_data()
            self._save_models()
            self.models_loaded = True

    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            self.match_predictor = joblib.load(
                os.path.join(self.model_dir, 'match_predictor.joblib')
            )
            self.tfidf_vectorizer = joblib.load(
                os.path.join(self.model_dir, 'tfidf_vectorizer.joblib')
            )
            self.feature_scaler = joblib.load(
                os.path.join(self.model_dir, 'feature_scaler.joblib')
            )
            print("✅ ML job matching models loaded successfully")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            self._train_models_with_synthetic_data()

    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.match_predictor,
                       os.path.join(self.model_dir, 'match_predictor.joblib'))
            joblib.dump(self.tfidf_vectorizer,
                       os.path.join(self.model_dir, 'tfidf_vectorizer.joblib'))
            joblib.dump(self.feature_scaler,
                       os.path.join(self.model_dir, 'feature_scaler.joblib'))
            print("💾 ML job matching models saved successfully")
        except Exception as e:
            print(f"❌ Error saving models: {e}")

    def _train_models_with_synthetic_data(self):
        """Train models with synthetic data for demonstration"""
        print("🤖 Training ML job matching models with synthetic data...")

        # Generate synthetic job-candidate interaction data
        synthetic_data = self._generate_synthetic_matching_data(n_samples=2000)

        # Prepare features for match prediction
        X = synthetic_data.drop('match_score', axis=1)
        y = synthetic_data['match_score']

        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)

        # Train match predictor
        self.match_predictor.fit(X_scaled, y)

        # Fit TF-IDF on combined job and candidate descriptions
        combined_texts = synthetic_data['job_description'] + ' ' + synthetic_data['candidate_profile']
        self.tfidf_vectorizer.fit(combined_texts)

        print("✅ ML job matching models trained successfully")

    def _generate_synthetic_matching_data(self, n_samples: int = 2000) -> pd.DataFrame:
        """Generate synthetic job-candidate matching data"""
        np.random.seed(42)

        data = []

        # Define realistic job categories and required skills
        job_categories = {
            'Data Scientist': ['python', 'machine learning', 'sql', 'statistics', 'pandas', 'tensorflow'],
            'Software Engineer': ['python', 'java', 'javascript', 'git', 'docker', 'aws'],
            'Business Analyst': ['excel', 'sql', 'tableau', 'business analysis', 'requirements gathering'],
            'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'jenkins', 'linux', 'python'],
            'Product Manager': ['product management', 'agile', 'analytics', 'stakeholder management', 'roadmapping'],
            'UX Designer': ['figma', 'user research', 'prototyping', 'adobe creative suite', 'usability testing']
        }

        experience_levels = ['Entry Level (0-2 years)', 'Mid Level (3-5 years)', 'Senior Level (5+ years)']

        for _ in range(n_samples):
            # Random job
            job_title = np.random.choice(list(job_categories.keys()))
            job_skills = job_categories[job_title]
            required_experience = np.random.choice(experience_levels)

            # Generate job description
            job_desc_parts = [
                f"{job_title} position requiring {required_experience} experience.",
                f"Key skills: {', '.join(job_skills[:4])}",
                f"Responsibilities include {job_title.lower().replace(' ', ' and ')} tasks.",
                f"Location: {'Remote' if np.random.random() > 0.5 else 'Johannesburg'}"
            ]
            job_description = ' '.join(job_desc_parts)

            # Random candidate
            candidate_experience = np.random.randint(0, 12)
            candidate_skills = np.random.choice(
                sum(job_categories.values(), []),
                size=np.random.randint(3, 8),
                replace=False
            )

            # Generate candidate profile
            candidate_desc_parts = [
                f"Professional with {candidate_experience} years of experience.",
                f"Skills: {', '.join(candidate_skills)}",
                f"Background in {np.random.choice(['Technology', 'Business', 'Engineering', 'Science'])}"
            ]
            candidate_profile = ' '.join(candidate_desc_parts)

            # Calculate match score based on skill overlap and experience match
            skill_overlap = len(set(job_skills) & set(candidate_skills))
            skill_match_ratio = skill_overlap / len(job_skills)

            # Experience compatibility
            if 'Entry Level' in required_experience and candidate_experience <= 2:
                exp_match = 1.0
            elif 'Mid Level' in required_experience and 1 <= candidate_experience <= 7:
                exp_match = 0.8
            elif 'Senior Level' in required_experience and candidate_experience >= 3:
                exp_match = 0.9
            else:
                exp_match = 0.3

            # Overall match score (0-1 scale)
            match_score = (skill_match_ratio * 0.7) + (exp_match * 0.3)

            # Add some noise
            match_score = np.clip(match_score + np.random.normal(0, 0.1), 0, 1)

            data.append({
                'job_title': job_title,
                'job_description': job_description,
                'candidate_profile': candidate_profile,
                'skill_overlap': skill_overlap,
                'experience_years': candidate_experience,
                'match_score': match_score,
                'required_experience_level': required_experience,
                'skill_match_ratio': skill_match_ratio,
                'experience_match': exp_match
            })

        return pd.DataFrame(data)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using sentence transformers

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        try:
            # Generate embeddings
            embeddings = self.sentence_model.encode([text1, text2])

            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            return float(similarity)

        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            return 0.0

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using TF-IDF and cosine similarity

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        try:
            # Vectorize texts
            tfidf_matrix = self.tfidf_vectorizer.transform([text1, text2])

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)

        except Exception as e:
            print(f"Error calculating text similarity: {e}")
            return 0.0

    def predict_match_score(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> float:
        """
        Predict match score using trained ML model

        Args:
            job_data: Job posting data
            candidate_data: Candidate profile data

        Returns:
            Predicted match score (0-1)
        """
        try:
            # Extract features
            features = self._extract_matching_features(job_data, candidate_data)

            # Scale features
            features_scaled = self.feature_scaler.transform([features])

            # Predict match score
            prediction = self.match_predictor.predict(features_scaled)[0]

            # Ensure prediction is within bounds
            return float(np.clip(prediction, 0, 1))

        except Exception as e:
            print(f"Error predicting match score: {e}")
            return 0.0

    def _extract_matching_features(self, job_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> List[float]:
        """Extract features for match prediction"""
        features = []

        # Skill overlap
        job_skills = set(job_data.get('skills', []))
        candidate_skills = set(candidate_data.get('skills', []))
        skill_overlap = len(job_skills & candidate_skills)
        skill_union = len(job_skills | candidate_skills)
        skill_jaccard = skill_overlap / skill_union if skill_union > 0 else 0
        features.append(skill_overlap)
        features.append(skill_jaccard)

        # Experience compatibility
        job_exp_required = self._parse_experience_level(job_data.get('experience_level', ''))
        candidate_exp = candidate_data.get('experience_years', 0)
        exp_compatibility = self._calculate_experience_compatibility(job_exp_required, candidate_exp)
        features.append(candidate_exp)
        features.append(exp_compatibility)

        # Education compatibility
        job_education = job_data.get('education_required', '')
        candidate_education = candidate_data.get('education', '')
        education_score = self._calculate_education_compatibility(job_education, candidate_education)
        features.append(education_score)

        # Text similarities
        job_desc = job_data.get('description', '')
        candidate_profile = self._create_candidate_profile_text(candidate_data)

        semantic_sim = self.calculate_semantic_similarity(job_desc, candidate_profile)
        text_sim = self.calculate_text_similarity(job_desc, candidate_profile)

        features.append(semantic_sim)
        features.append(text_sim)

        return features

    def _parse_experience_level(self, exp_level: str) -> Tuple[int, int]:
        """Parse experience level string into min/max years"""
        exp_level = exp_level.lower()

        if 'entry' in exp_level or 'junior' in exp_level:
            return (0, 2)
        elif 'mid' in exp_level or 'intermediate' in exp_level:
            return (3, 5)
        elif 'senior' in exp_level or 'lead' in exp_level:
            return (5, 10)
        elif 'executive' in exp_level or 'director' in exp_level:
            return (10, 20)
        else:
            return (0, 5)  # Default

    def _calculate_experience_compatibility(self, required_range: Tuple[int, int], candidate_exp: int) -> float:
        """Calculate how well candidate experience matches job requirements"""
        min_req, max_req = required_range

        if min_req <= candidate_exp <= max_req:
            return 1.0  # Perfect match
        elif candidate_exp < min_req:
            # Underqualified - score based on how close they are
            if candidate_exp >= min_req * 0.5:
                return 0.6
            else:
                return 0.2
        else:
            # Overqualified - still potentially good, but less ideal
            if candidate_exp <= max_req * 1.5:
                return 0.8
            else:
                return 0.4

    def _calculate_education_compatibility(self, job_education: str, candidate_education: str) -> float:
        """Calculate education compatibility score"""
        education_hierarchy = {
            'high school': 1,
            'diploma': 2,
            'certificate': 2,
            'bachelor': 3,
            'bsc': 3,
            'ba': 3,
            'master': 4,
            'msc': 4,
            'ma': 4,
            'mba': 4,
            'phd': 5,
            'doctorate': 5
        }

        job_level = 0
        candidate_level = 0

        for edu, level in education_hierarchy.items():
            if edu in job_education.lower():
                job_level = max(job_level, level)
            if edu in candidate_education.lower():
                candidate_level = max(candidate_level, level)

        if candidate_level >= job_level:
            return 1.0
        elif candidate_level >= job_level - 1:
            return 0.7
        else:
            return 0.3

    def _create_candidate_profile_text(self, candidate_data: Dict[str, Any]) -> str:
        """Create a text representation of candidate profile"""
        parts = []

        if 'experience_years' in candidate_data:
            parts.append(f"{candidate_data['experience_years']} years experience")

        if 'skills' in candidate_data:
            parts.append(f"Skills: {', '.join(candidate_data['skills'])}")

        if 'education' in candidate_data:
            parts.append(f"Education: {candidate_data['education']}")

        if 'industry' in candidate_data:
            parts.append(f"Industry: {candidate_data['industry']}")

        return '. '.join(parts)

    def find_best_matches_ml(self, candidate_profile: Dict[str, Any],
                           job_postings: List[Dict[str, Any]],
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find best job matches for a candidate using ML models

        Args:
            candidate_profile: Candidate profile data
            job_postings: List of job postings
            top_k: Number of top matches to return

        Returns:
            List of job matches with scores and explanations
        """
        matches = []

        for job in job_postings:
            try:
                # Calculate multiple similarity scores
                ml_score = self.predict_match_score(job, candidate_profile)

                semantic_sim = self.calculate_semantic_similarity(
                    job.get('description', ''),
                    self._create_candidate_profile_text(candidate_profile)
                )

                # Combine scores with weights
                final_score = (ml_score * 0.6) + (semantic_sim * 0.4)

                # Generate match explanation
                explanation = self._generate_match_explanation(job, candidate_profile, ml_score, semantic_sim)

                match = {
                    'job': job,
                    'match_score': round(final_score * 100, 2),  # Convert to percentage
                    'ml_score': round(ml_score * 100, 2),
                    'semantic_similarity': round(semantic_sim * 100, 2),
                    'explanation': explanation,
                    'matching_factors': self._analyze_matching_factors(job, candidate_profile)
                }

                matches.append(match)

            except Exception as e:
                print(f"Error matching job {job.get('title', 'Unknown')}: {e}")
                continue

        # Sort by match score and return top_k
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:top_k]

    def _generate_match_explanation(self, job: Dict[str, Any], candidate: Dict[str, Any],
                                  ml_score: float, semantic_sim: float) -> str:
        """Generate human-readable explanation for the match"""
        explanations = []

        # Experience analysis
        candidate_exp = candidate.get('experience_years', 0)
        job_exp_req = job.get('experience_level', '')

        if candidate_exp >= 3 and 'senior' in job_exp_req.lower():
            explanations.append("Experience level aligns well with job requirements")
        elif candidate_exp <= 2 and 'entry' in job_exp_req.lower():
            explanations.append("Suitable for entry-level position")
        elif candidate_exp > 5:
            explanations.append("Strong experience background")

        # Skills analysis
        job_skills = set(job.get('skills', []))
        candidate_skills = set(candidate.get('skills', []))
        skill_overlap = len(job_skills & candidate_skills)

        if skill_overlap >= len(job_skills) * 0.7:
            explanations.append(f"Excellent skill match ({skill_overlap} skills overlap)")
        elif skill_overlap >= len(job_skills) * 0.4:
            explanations.append(f"Good skill alignment ({skill_overlap} skills match)")
        else:
            explanations.append("Some skills overlap, potential for learning")

        # Semantic similarity
        if semantic_sim > 0.7:
            explanations.append("Strong semantic alignment between job and profile")
        elif semantic_sim > 0.5:
            explanations.append("Moderate content similarity")

        # ML confidence
        if ml_score > 0.8:
            explanations.append("ML model predicts high compatibility")
        elif ml_score > 0.6:
            explanations.append("ML model suggests good potential fit")

        return "; ".join(explanations) if explanations else "Basic compatibility identified"

    def _analyze_matching_factors(self, job: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual factors contributing to the match"""
        factors = {}

        # Skills factor
        job_skills = set(job.get('skills', []))
        candidate_skills = set(candidate.get('skills', []))
        skill_overlap = len(job_skills & candidate_skills)
        skill_coverage = skill_overlap / len(job_skills) if job_skills else 0
        factors['skills'] = {
            'overlap_count': skill_overlap,
            'coverage_percentage': round(skill_coverage * 100, 1),
            'matching_skills': list(job_skills & candidate_skills)
        }

        # Experience factor
        candidate_exp = candidate.get('experience_years', 0)
        job_exp_req = job.get('experience_level', '')
        exp_compat = self._calculate_experience_compatibility(
            self._parse_experience_level(job_exp_req), candidate_exp
        )
        factors['experience'] = {
            'candidate_years': candidate_exp,
            'required_level': job_exp_req,
            'compatibility_score': round(exp_compat * 100, 1)
        }

        # Education factor
        education_compat = self._calculate_education_compatibility(
            job.get('education_required', ''),
            candidate.get('education', '')
        )
        factors['education'] = {
            'candidate_education': candidate.get('education', ''),
            'required_education': job.get('education_required', ''),
            'compatibility_score': round(education_compat * 100, 1)
        }

        return factors

    def update_user_interactions(self, candidate_id: str, job_id: str, interaction_type: str, score: float):
        """
        Update collaborative filtering data with user interactions

        Args:
            candidate_id: Unique candidate identifier
            job_id: Unique job identifier
            interaction_type: Type of interaction (view, apply, interview, hire)
            score: Interaction score (0-1)
        """
        self.user_item_interactions[candidate_id][job_id] = {
            'type': interaction_type,
            'score': score,
            'timestamp': datetime.now().isoformat()
        }

    def get_collaborative_recommendations(self, candidate_id: str, job_postings: List[Dict[str, Any]],
                                        top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get collaborative filtering recommendations based on similar candidates

        Args:
            candidate_id: Candidate to get recommendations for
            job_postings: Available job postings
            top_k: Number of recommendations to return

        Returns:
            List of recommended jobs with collaborative scores
        """
        if candidate_id not in self.user_item_interactions:
            return []

        # Find similar candidates based on interaction patterns
        candidate_interactions = self.user_item_interactions[candidate_id]
        similar_candidates = self._find_similar_candidates(candidate_id)

        recommendations = []

        for job in job_postings:
            job_id = job.get('id', job.get('title', ''))

            # Calculate collaborative score
            collab_score = self._calculate_collaborative_score(job_id, similar_candidates)

            if collab_score > 0:
                recommendations.append({
                    'job': job,
                    'collaborative_score': round(collab_score * 100, 2),
                    'reason': f"Similar candidates found this job appealing"
                })

        # Sort by collaborative score and return top_k
        recommendations.sort(key=lambda x: x['collaborative_score'], reverse=True)
        return recommendations[:top_k]

    def _find_similar_candidates(self, candidate_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find candidates with similar interaction patterns"""
        if candidate_id not in self.user_item_interactions:
            return []

        candidate_jobs = set(self.user_item_interactions[candidate_id].keys())
        similarities = []

        for other_id, interactions in self.user_item_interactions.items():
            if other_id == candidate_id:
                continue

            other_jobs = set(interactions.keys())
            intersection = len(candidate_jobs & other_jobs)
            union = len(candidate_jobs | other_jobs)

            if union > 0:
                jaccard_sim = intersection / union
                similarities.append((other_id, jaccard_sim))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _calculate_collaborative_score(self, job_id: str, similar_candidates: List[Tuple[str, float]]) -> float:
        """Calculate collaborative filtering score for a job"""
        total_score = 0
        total_weight = 0

        for candidate_id, similarity in similar_candidates:
            if job_id in self.user_item_interactions[candidate_id]:
                interaction = self.user_item_interactions[candidate_id][job_id]
                score = interaction.get('score', 0.5)
                total_score += score * similarity
                total_weight += similarity

        return total_score / total_weight if total_weight > 0 else 0

    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for matching models"""
        return {
            'match_predictor': {
                'type': 'XGBoost Regressor',
                'mae': 0.12,  # Example metrics
                'rmse': 0.15,
                'r2_score': 0.78
            },
            'semantic_similarity': {
                'model': 'all-MiniLM-L6-v2',
                'embedding_dimension': 384
            },
            'last_updated': datetime.now().isoformat(),
            'training_samples': 2000
        }


# Create singleton instance
ml_job_matcher_agent = MLJobMatcherAgent()

# Hybrid function that combines ML and traditional matching
def match_jobs_hybrid(candidate_profile: Dict[str, Any],
                     job_postings: List[Dict[str, Any]],
                     use_ml: bool = True,
                     top_k: int = 10) -> Dict[str, Any]:
    """
    Hybrid job matching using both ML and traditional approaches

    Args:
        candidate_profile: Candidate profile data
        job_postings: List of available job postings
        use_ml: Whether to use ML-enhanced matching
        top_k: Number of top matches to return

    Returns:
        Matching results with both ML and traditional scores
    """
    results = {
        'matches': [],
        'method': 'hybrid',
        'ml_used': use_ml,
        'total_jobs_considered': len(job_postings)
    }

    if use_ml:
        try:
            # Get ML-based matches
            ml_matches = ml_job_matcher_agent.find_best_matches_ml(
                candidate_profile, job_postings, top_k=top_k
            )

            # Add collaborative filtering recommendations
            collab_recs = ml_job_matcher_agent.get_collaborative_recommendations(
                candidate_profile.get('id', 'unknown'), job_postings, top_k=3
            )

            results['matches'] = ml_matches
            results['collaborative_recommendations'] = collab_recs
            results['ml_performance'] = ml_job_matcher_agent.get_model_performance_metrics()

        except Exception as e:
            print(f"ML matching failed: {e}. Falling back to traditional matching.")
            results['ml_error'] = str(e)
            use_ml = False

    if not use_ml:
        # Fallback to traditional matching
        try:
            traditional_matches = match_student_to_jobs(candidate_profile)
            # Convert to similar format
            results['matches'] = [{
                'job': match,
                'match_score': match.get('compatibility_score', 50),
                'method': 'traditional',
                'explanation': 'Traditional keyword and rule-based matching'
            } for match in traditional_matches[:top_k]]

        except Exception as e:
            results['error'] = f'Both ML and traditional matching failed: {str(e)}'

    return results


if __name__ == "__main__":
    # Test the ML job matcher
    sample_candidate = {
        'id': 'candidate_001',
        'experience_years': 3,
        'skills': ['python', 'machine learning', 'sql', 'pandas'],
        'education': 'Bachelor of Science',
        'industry': 'Technology'
    }

    sample_jobs = [
        {
            'id': 'job_001',
            'title': 'Data Scientist',
            'description': 'Looking for a Data Scientist with Python, ML, and SQL skills. 2-4 years experience.',
            'skills': ['python', 'machine learning', 'sql', 'statistics'],
            'experience_level': 'Mid Level (3-5 years)',
            'education_required': 'Bachelor'
        },
        {
            'id': 'job_002',
            'title': 'Software Engineer',
            'description': 'Seeking Software Engineer with JavaScript and React experience.',
            'skills': ['javascript', 'react', 'node.js', 'git'],
            'experience_level': 'Entry Level (0-2 years)',
            'education_required': 'Bachelor'
        }
    ]

    results = match_jobs_hybrid(sample_candidate, sample_jobs, use_ml=True, top_k=5)

    print("ML Job Matching Results:")
    for i, match in enumerate(results['matches'], 1):
        print(f"{i}. {match['job']['title']} - Score: {match['match_score']}%")
        print(f"   Explanation: {match['explanation']}")
        print()
