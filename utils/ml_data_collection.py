"""
ML Data Collection Strategy for CareerBoost AI
Comprehensive data collection, management, and pipeline system for ML training
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataCollectionConfig:
    """Configuration for data collection pipeline"""
    data_dir: str = "ml_training_data"
    anonymize_data: bool = True
    retention_days: int = 2555  # 7 years for POPIA compliance
    batch_size: int = 1000
    quality_threshold: float = 0.8
    synthetic_data_ratio: float = 0.3  # 30% synthetic, 70% real

class MLDataCollectionStrategy:
    """
    Comprehensive data collection strategy for ML training across all agents.
    Handles synthetic data generation, real data anonymization, and quality assurance.
    """

    def __init__(self, config: Optional[DataCollectionConfig] = None):
        """
        Initialize the data collection strategy

        Args:
            config: Data collection configuration
        """
        self.config = config or DataCollectionConfig()
        self.data_sources = {}
        self.quality_metrics = {}
        self.anonymization_map = {}

        # Create data directories
        self._setup_data_directories()

        # Initialize data collection for each agent type
        self._initialize_agent_data_requirements()

    def _setup_data_directories(self):
        """Create organized data directory structure"""
        directories = [
            self.config.data_dir,
            f"{self.config.data_dir}/raw",
            f"{self.config.data_dir}/processed",
            f"{self.config.data_dir}/synthetic",
            f"{self.config.data_dir}/anonymized",
            f"{self.config.data_dir}/quality_checks",
            f"{self.config.data_dir}/metadata"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _initialize_agent_data_requirements(self):
        """Define data requirements for each ML agent"""

        self.agent_data_requirements = {
            'resume_screening': {
                'data_types': ['resume_text', 'qualification_labels', 'industry_labels'],
                'sample_size_target': 10000,
                'features': [
                    'full_text', 'entities_extracted', 'skills_list',
                    'experience_years', 'education_level', 'qualification_outcome'
                ],
                'label_types': ['qualified', 'maybe', 'unqualified']
            },

            'candidate_ranking': {
                'data_types': ['candidate_profiles', 'ranking_scores', 'hire_outcomes'],
                'sample_size_target': 5000,
                'features': [
                    'experience_years', 'education_level', 'skills_count',
                    'skill_relevance_score', 'previous_companies', 'final_ranking'
                ],
                'label_types': ['hire_outcome', 'ranking_score']
            },

            'job_matching': {
                'data_types': ['job_postings', 'candidate_profiles', 'match_scores'],
                'sample_size_target': 8000,
                'features': [
                    'job_description', 'candidate_profile', 'skill_overlap',
                    'experience_match', 'semantic_similarity', 'final_match_score'
                ],
                'label_types': ['match_quality', 'application_outcome']
            },

            'predictive_analytics': {
                'data_types': ['hire_history', 'performance_data', 'market_trends'],
                'sample_size_target': 3000,
                'features': [
                    'time_to_hire', 'retention_duration', 'performance_ratings',
                    'market_conditions', 'candidate_characteristics'
                ],
                'label_types': ['hire_success', 'retention_outcome', 'performance_score']
            },

            'profile_builder': {
                'data_types': ['career_trajectories', 'skill_gaps', 'development_paths'],
                'sample_size_target': 4000,
                'features': [
                    'current_skills', 'target_role', 'skill_gaps',
                    'learning_velocity', 'career_progression'
                ],
                'label_types': ['trajectory_prediction', 'skill_gap_analysis']
            },

            'interview_assistant': {
                'data_types': ['interview_transcripts', 'sentiment_labels', 'behavioral_cues'],
                'sample_size_target': 2000,
                'features': [
                    'response_text', 'sentiment_score', 'confidence_indicators',
                    'behavioral_patterns', 'question_type'
                ],
                'label_types': ['sentiment', 'confidence_level', 'behavioral_assessment']
            }
        }

    def generate_synthetic_training_data(self, agent_type: str, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic training data for a specific agent type

        Args:
            agent_type: Type of agent (resume_screening, candidate_ranking, etc.)
            n_samples: Number of samples to generate

        Returns:
            DataFrame with synthetic training data
        """
        if agent_type not in self.agent_data_requirements:
            raise ValueError(f"Unknown agent type: {agent_type}")

        requirements = self.agent_data_requirements[agent_type]

        if agent_type == 'resume_screening':
            return self._generate_resume_screening_data(n_samples)
        elif agent_type == 'candidate_ranking':
            return self._generate_candidate_ranking_data(n_samples)
        elif agent_type == 'job_matching':
            return self._generate_job_matching_data(n_samples)
        elif agent_type == 'predictive_analytics':
            return self._generate_predictive_analytics_data(n_samples)
        elif agent_type == 'profile_builder':
            return self._generate_profile_builder_data(n_samples)
        elif agent_type == 'interview_assistant':
            return self._generate_interview_assistant_data(n_samples)
        else:
            raise ValueError(f"Synthetic data generation not implemented for: {agent_type}")

    def _generate_resume_screening_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic resume screening data"""
        np.random.seed(42)

        data = []

        # Realistic data distributions
        industries = ['Technology', 'Finance', 'Healthcare', 'Consulting', 'Marketing', 'Engineering']
        education_levels = ['High School', 'Diploma', 'Bachelor', 'Master', 'PhD']
        experience_ranges = [(0, 2), (3, 5), (6, 10), (11, 15), (16, 20)]

        for _ in range(n_samples):
            industry = np.random.choice(industries)
            exp_min, exp_max = np.random.choice(experience_ranges)
            experience_years = np.random.randint(exp_min, exp_max + 1)
            education = np.random.choice(education_levels,
                                       p=[0.1, 0.2, 0.5, 0.15, 0.05])  # Bachelor most common

            # Generate skills based on industry
            skills = self._generate_industry_skills(industry, experience_years)

            # Create synthetic resume text
            resume_text = self._create_synthetic_resume_text(
                industry, experience_years, education, skills
            )

            # Determine qualification based on realistic criteria
            qualification = self._determine_qualification_realistically(
                experience_years, education, skills, industry
            )

            data.append({
                'resume_text': resume_text,
                'industry': industry,
                'experience_years': experience_years,
                'education': education,
                'skills': skills,
                'qualification': qualification,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    def _generate_candidate_ranking_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic candidate ranking data"""
        np.random.seed(43)

        data = []

        for _ in range(n_samples):
            # Generate candidate characteristics
            experience_years = np.random.randint(0, 15)
            education_level = np.random.choice(['Bachelor', 'Master', 'PhD'],
                                             p=[0.7, 0.25, 0.05])
            skills_count = np.random.randint(3, 12)

            # Calculate component scores
            skill_score = min(skills_count / 10, 1.0)
            experience_score = min(experience_years / 10, 1.0)
            education_score = {'Bachelor': 0.6, 'Master': 0.8, 'PhD': 1.0}[education_level]

            # Overall ranking score (0-100)
            base_score = (
                skill_score * 40 +      # Skills (40%)
                experience_score * 35 + # Experience (35%)
                education_score * 25    # Education (25%)
            )

            # Add realistic noise
            ranking_score = np.clip(base_score + np.random.normal(0, 8), 0, 100)

            # Simulated hire outcome (higher scores more likely to be hired)
            hire_probability = ranking_score / 100
            hire_outcome = np.random.random() < hire_probability

            data.append({
                'experience_years': experience_years,
                'education_level': education_level,
                'skills_count': skills_count,
                'skill_score': skill_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'ranking_score': ranking_score,
                'hire_outcome': hire_outcome,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    def _generate_job_matching_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic job matching data"""
        np.random.seed(44)

        data = []

        job_types = ['Data Scientist', 'Software Engineer', 'Business Analyst',
                    'DevOps Engineer', 'Product Manager', 'UX Designer']

        for _ in range(n_samples):
            # Generate job posting
            job_title = np.random.choice(job_types)
            job_skills = self._get_job_required_skills(job_title)

            # Generate candidate
            candidate_exp = np.random.randint(0, 12)
            candidate_skills = np.random.choice(
                list(set(sum(self._get_all_skills(), []))),  # All possible skills
                size=np.random.randint(3, 8),
                replace=False
            )

            # Calculate match factors
            skill_overlap = len(set(job_skills) & set(candidate_skills))
            skill_coverage = skill_overlap / len(job_skills) if job_skills else 0

            # Experience compatibility
            exp_compat = self._calculate_experience_compatibility(
                self._get_job_experience_req(job_title), candidate_exp
            )

            # Overall match score
            match_score = (skill_coverage * 0.6) + (exp_compat * 0.4)
            match_score = np.clip(match_score + np.random.normal(0, 0.1), 0, 1)

            data.append({
                'job_title': job_title,
                'job_skills': job_skills,
                'candidate_experience': candidate_exp,
                'candidate_skills': candidate_skills,
                'skill_overlap': skill_overlap,
                'skill_coverage': skill_coverage,
                'experience_compatibility': exp_compat,
                'match_score': match_score,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    def _generate_predictive_analytics_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic predictive analytics data"""
        np.random.seed(45)

        data = []

        for _ in range(n_samples):
            # Simulate hiring process data
            time_to_hire = np.random.randint(7, 90)  # Days
            candidate_quality_score = np.random.uniform(0, 100)

            # Simulate retention (higher quality candidates stay longer)
            retention_probability = min(candidate_quality_score / 100, 0.9)
            retained = np.random.random() < retention_probability

            retention_months = np.random.randint(3, 36) if retained else np.random.randint(1, 12)

            # Performance rating (correlated with quality score)
            performance_rating = np.clip(
                candidate_quality_score / 20 + np.random.normal(0, 0.5), 1, 5
            )

            data.append({
                'time_to_hire_days': time_to_hire,
                'candidate_quality_score': candidate_quality_score,
                'retained': retained,
                'retention_months': retention_months,
                'performance_rating': performance_rating,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    def _generate_profile_builder_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic profile builder data"""
        np.random.seed(46)

        data = []

        career_paths = ['Individual Contributor', 'Management', 'Technical Leadership']

        for _ in range(n_samples):
            # Current state
            current_experience = np.random.randint(0, 10)
            current_skills = np.random.choice(
                ['python', 'sql', 'excel', 'leadership', 'project_management'],
                size=np.random.randint(2, 6),
                replace=False
            )

            # Target role
            target_path = np.random.choice(career_paths)
            target_experience_needed = current_experience + np.random.randint(2, 8)

            # Calculate skill gaps
            target_skills = self._get_target_skills_for_path(target_path)
            skill_gaps = list(set(target_skills) - set(current_skills))
            skill_gap_count = len(skill_gaps)

            # Learning velocity assessment
            learning_velocity = np.random.choice(['Fast', 'Moderate', 'Steady'],
                                               p=[0.3, 0.5, 0.2])

            data.append({
                'current_experience_years': current_experience,
                'current_skills': current_skills,
                'target_career_path': target_path,
                'target_experience_needed': target_experience_needed,
                'skill_gaps': skill_gaps,
                'skill_gap_count': skill_gap_count,
                'learning_velocity': learning_velocity,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    def _generate_interview_assistant_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic interview assistant data"""
        np.random.seed(47)

        data = []

        question_types = ['Technical', 'Behavioral', 'Situational', 'Company Culture']
        confidence_levels = ['Low', 'Medium', 'High']
        sentiment_labels = ['Negative', 'Neutral', 'Positive']

        for _ in range(n_samples):
            question_type = np.random.choice(question_types)
            response_length = np.random.randint(50, 500)  # Characters

            # Generate synthetic response based on question type
            response_text = self._generate_interview_response(question_type, response_length)

            # Simulated analysis results
            sentiment = np.random.choice(sentiment_labels, p=[0.2, 0.5, 0.3])
            confidence = np.random.choice(confidence_levels, p=[0.3, 0.5, 0.2])

            # Behavioral cues (simplified)
            behavioral_score = np.random.uniform(0, 1)
            if sentiment == 'Positive':
                behavioral_score = min(behavioral_score + 0.3, 1.0)
            elif sentiment == 'Negative':
                behavioral_score = max(behavioral_score - 0.3, 0.0)

            data.append({
                'question_type': question_type,
                'response_text': response_text,
                'response_length': response_length,
                'sentiment': sentiment,
                'confidence_level': confidence,
                'behavioral_score': behavioral_score,
                'data_type': 'synthetic',
                'generated_at': datetime.now().isoformat()
            })

        return pd.DataFrame(data)

    # Helper methods for synthetic data generation
    def _generate_industry_skills(self, industry: str, experience_years: int) -> List[str]:
        """Generate realistic skills for an industry and experience level"""
        industry_skill_map = {
            'Technology': ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'git'],
            'Finance': ['excel', 'financial analysis', 'accounting', 'sql', 'sap', 'bloomberg'],
            'Healthcare': ['patient care', 'medical records', 'hipaa', 'nursing', 'ehr'],
            'Consulting': ['business analysis', 'stakeholder management', 'sql', 'powerpoint'],
            'Marketing': ['digital marketing', 'seo', 'social media', 'google analytics', 'adobe'],
            'Engineering': ['cad', 'solidworks', 'project management', 'quality control', 'matlab']
        }

        base_skills = industry_skill_map.get(industry, [])
        n_skills = min(len(base_skills), max(3, experience_years // 2 + 1))

        return np.random.choice(base_skills, size=n_skills, replace=False).tolist()

    def _create_synthetic_resume_text(self, industry: str, experience: int,
                                    education: str, skills: List[str]) -> str:
        """Create realistic synthetic resume text"""
        parts = [
            f"Professional with {experience} years of experience in {industry}.",
            f"Education: {education} degree in relevant field.",
            f"Skills: {', '.join(skills)}.",
            f"Previous roles include {industry.lower()} positions with increasing responsibility."
        ]
        return ' '.join(parts)

    def _determine_qualification_realistically(self, experience: int, education: str,
                                            skills: List[str], industry: str) -> str:
        """Realistic qualification determination"""
        score = 0

        # Experience scoring
        if experience >= 5:
            score += 40
        elif experience >= 2:
            score += 25
        else:
            score += 10

        # Education scoring
        education_scores = {'High School': 5, 'Diploma': 10, 'Bachelor': 20, 'Master': 25, 'PhD': 30}
        score += education_scores.get(education, 10)

        # Skills scoring
        score += min(len(skills) * 3, 30)

        # Determine qualification
        if score >= 60:
            return 'QUALIFIED'
        elif score >= 35:
            return 'MAYBE'
        else:
            return 'UNQUALIFIED'

    def _get_job_required_skills(self, job_title: str) -> List[str]:
        """Get required skills for a job title"""
        skill_map = {
            'Data Scientist': ['python', 'machine learning', 'sql', 'statistics'],
            'Software Engineer': ['python', 'java', 'git', 'testing'],
            'Business Analyst': ['sql', 'excel', 'business analysis', 'reporting'],
            'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'ci/cd'],
            'Product Manager': ['product management', 'agile', 'analytics'],
            'UX Designer': ['figma', 'user research', 'prototyping']
        }
        return skill_map.get(job_title, [])

    def _get_all_skills(self) -> List[List[str]]:
        """Get all possible skills across industries"""
        return [
            ['python', 'java', 'javascript', 'sql', 'aws', 'docker'],
            ['excel', 'financial analysis', 'accounting', 'sap'],
            ['patient care', 'medical records', 'nursing'],
            ['business analysis', 'stakeholder management', 'powerpoint'],
            ['digital marketing', 'seo', 'social media', 'google analytics'],
            ['cad', 'solidworks', 'project management']
        ]

    def _get_job_experience_req(self, job_title: str) -> Tuple[int, int]:
        """Get experience requirements for job title"""
        exp_map = {
            'Data Scientist': (2, 5),
            'Software Engineer': (1, 4),
            'Business Analyst': (1, 3),
            'DevOps Engineer': (3, 6),
            'Product Manager': (3, 7),
            'UX Designer': (1, 4)
        }
        return exp_map.get(job_title, (0, 3))

    def _calculate_experience_compatibility(self, required_range: Tuple[int, int],
                                          candidate_exp: int) -> float:
        """Calculate experience compatibility score"""
        min_req, max_req = required_range

        if min_req <= candidate_exp <= max_req:
            return 1.0
        elif candidate_exp < min_req:
            return max(0.2, candidate_exp / min_req)
        else:
            return max(0.5, 1.0 - (candidate_exp - max_req) / (max_req * 0.5))

    def _get_target_skills_for_path(self, career_path: str) -> List[str]:
        """Get target skills for career path"""
        path_skills = {
            'Individual Contributor': ['technical_expertise', 'problem_solving', 'domain_knowledge'],
            'Management': ['leadership', 'communication', 'project_management', 'team_building'],
            'Technical Leadership': ['technical_expertise', 'leadership', 'mentoring', 'architecture']
        }
        return path_skills.get(career_path, [])

    def _generate_interview_response(self, question_type: str, length: int) -> str:
        """Generate synthetic interview response"""
        templates = {
            'Technical': "When faced with this technical challenge, I approached it by first analyzing the requirements, then implementing a solution using best practices. The key was understanding the underlying architecture and ensuring scalability.",
            'Behavioral': "In my previous role, I demonstrated leadership by taking initiative on a project that needed direction. I coordinated with team members, delegated tasks effectively, and delivered results ahead of schedule.",
            'Situational': "If I encountered this situation, I would first gather all relevant information, consult with stakeholders, and develop a systematic approach to resolve the issue while minimizing impact.",
            'Company Culture': "I'm drawn to companies that value innovation and collaboration. I thrive in environments where I can contribute ideas, learn from colleagues, and grow professionally while making a meaningful impact."
        }

        base_response = templates.get(question_type, "This is a sample response to the interview question.")
        # Extend response to desired length (simplified)
        return base_response + " " + "I believe this approach demonstrates my problem-solving abilities and commitment to excellence."

    def anonymize_personal_data(self, data: pd.DataFrame,
                              sensitive_columns: List[str] = None) -> pd.DataFrame:
        """
        Anonymize personal data in compliance with POPIA

        Args:
            data: DataFrame containing personal data
            sensitive_columns: Columns containing sensitive information

        Returns:
            Anonymized DataFrame
        """
        if not self.config.anonymize_data:
            return data

        if sensitive_columns is None:
            sensitive_columns = ['name', 'email', 'phone', 'address', 'id_number']

        anonymized_data = data.copy()

        for column in sensitive_columns:
            if column in anonymized_data.columns:
                # Create hash-based anonymization
                anonymized_data[column] = anonymized_data[column].apply(
                    lambda x: self._anonymize_value(x) if pd.notna(x) else x
                )

        return anonymized_data

    def _anonymize_value(self, value: str) -> str:
        """Anonymize a single value using hashing"""
        if not isinstance(value, str):
            return str(value)

        # Create consistent hash for same values
        hash_obj = hashlib.sha256(value.encode())
        return f"anon_{hash_obj.hexdigest()[:16]}"

    def validate_data_quality(self, data: pd.DataFrame, agent_type: str) -> Dict[str, Any]:
        """
        Validate data quality for training

        Args:
            data: DataFrame to validate
            agent_type: Type of agent data is for

        Returns:
            Quality validation results
        """
        quality_report = {
            'total_samples': len(data),
            'quality_score': 0.0,
            'issues': [],
            'recommendations': []
        }

        requirements = self.agent_data_requirements.get(agent_type, {})

        # Check required columns
        required_features = requirements.get('features', [])
        missing_columns = [col for col in required_features if col not in data.columns]

        if missing_columns:
            quality_report['issues'].append(f"Missing required columns: {missing_columns}")
            quality_report['recommendations'].append("Add missing feature columns to dataset")

        # Check for missing values
        missing_data = data.isnull().sum()
        high_missing_cols = missing_data[missing_data > len(data) * 0.1]

        if len(high_missing_cols) > 0:
            quality_report['issues'].append(f"High missing data in columns: {high_missing_cols.index.tolist()}")
            quality_report['recommendations'].append("Impute or remove missing data")

        # Check data distribution
        if 'qualification' in data.columns:
            qual_distribution = data['qualification'].value_counts(normalize=True)
            if qual_distribution.min() < 0.1:  # Any class less than 10%
                quality_report['issues'].append("Imbalanced target classes detected")
                quality_report['recommendations'].append("Consider oversampling minority classes")

        # Calculate overall quality score
        base_score = 1.0
        penalties = len(quality_report['issues']) * 0.1
        quality_report['quality_score'] = max(0.0, base_score - penalties)

        # Store quality metrics
        self.quality_metrics[agent_type] = quality_report

        return quality_report

    def create_data_collection_pipeline(self, agent_type: str) -> Dict[str, Any]:
        """
        Create a complete data collection pipeline for an agent type

        Args:
            agent_type: Type of agent to create pipeline for

        Returns:
            Pipeline configuration
        """
        pipeline = {
            'agent_type': agent_type,
            'data_sources': [],
            'collection_steps': [],
            'validation_steps': [],
            'storage_config': {}
        }

        requirements = self.agent_data_requirements.get(agent_type, {})

        # Define data sources
        if agent_type == 'resume_screening':
            pipeline['data_sources'] = [
                'synthetic_resume_generator',
                'anonymized_job_applications',
                'public_resume_datasets'
            ]
        elif agent_type == 'candidate_ranking':
            pipeline['data_sources'] = [
                'historical_hiring_data',
                'performance_reviews',
                'synthetic_candidate_profiles'
            ]
        # Add other agent types...

        # Define collection steps
        pipeline['collection_steps'] = [
            'extract_raw_data',
            'anonymize_sensitive_data',
            'validate_data_quality',
            'feature_engineering',
            'store_processed_data'
        ]

        # Define validation steps
        pipeline['validation_steps'] = [
            'schema_validation',
            'quality_checks',
            'bias_assessment',
            'privacy_compliance'
        ]

        # Storage configuration
        pipeline['storage_config'] = {
            'raw_data_path': f"{self.config.data_dir}/raw/{agent_type}",
            'processed_data_path': f"{self.config.data_dir}/processed/{agent_type}",
            'metadata_path': f"{self.config.data_dir}/metadata/{agent_type}_metadata.json"
        }

        return pipeline

    def export_data_summary(self) -> Dict[str, Any]:
        """Export comprehensive data collection summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(self.agent_data_requirements),
            'data_requirements': self.agent_data_requirements,
            'quality_metrics': self.quality_metrics,
            'anonymization_stats': {
                'total_records_anonymized': len(self.anonymization_map),
                'retention_policy_days': self.config.retention_days
            },
            'synthetic_data_ratio': self.config.synthetic_data_ratio,
            'collection_pipelines': {}
        }

        # Add pipeline summaries
        for agent_type in self.agent_data_requirements.keys():
            summary['collection_pipelines'][agent_type] = self.create_data_collection_pipeline(agent_type)

        # Save to file
        summary_path = f"{self.config.data_dir}/metadata/data_collection_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Data collection summary exported to {summary_path}")

        return summary

# Global instance
ml_data_strategy = MLDataCollectionStrategy()

# Utility functions for quick data generation
def generate_training_data(agent_type: str, n_samples: int = 1000) -> pd.DataFrame:
    """Quick utility to generate training data for any agent type"""
    return ml_data_strategy.generate_synthetic_training_data(agent_type, n_samples)

def validate_dataset_quality(data: pd.DataFrame, agent_type: str) -> Dict[str, Any]:
    """Quick utility to validate dataset quality"""
    return ml_data_strategy.validate_data_quality(data, agent_type)

if __name__ == "__main__":
    # Example usage
    print("🤖 ML Data Collection Strategy Demo")
    print("=" * 50)

    # Generate sample data for resume screening
    resume_data = generate_training_data('resume_screening', n_samples=100)
    print(f"✅ Generated {len(resume_data)} resume screening samples")
    print(f"Sample qualification distribution: {resume_data['qualification'].value_counts().to_dict()}")

    # Validate data quality
    quality_report = validate_dataset_quality(resume_data, 'resume_screening')
    print(f"✅ Data quality score: {quality_report['quality_score']:.2f}")
    if quality_report['issues']:
        print(f"⚠️ Issues found: {quality_report['issues']}")

    # Generate data for candidate ranking
    ranking_data = generate_training_data('candidate_ranking', n_samples=50)
    print(f"✅ Generated {len(ranking_data)} candidate ranking samples")
    print(".1f")

    # Export summary
    summary = ml_data_strategy.export_data_summary()
    print(f"✅ Data collection summary exported for {summary['total_agents']} agents")

    print("\n🎯 Data collection strategy ready for ML training!")
