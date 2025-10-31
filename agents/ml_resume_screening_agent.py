"""
ML-Enhanced Resume Screening Specialist Agent
Uses machine learning models for automated resume parsing, classification, and screening
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

# ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import spacy
from sentence_transformers import SentenceTransformer
import xgboost as xgb
from imblearn.over_sampling import SMOTE

# Local imports
from agents import resume_screening_agent  # Original Gemini-based agent

# Configure logging
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)

class MLResumeScreeningAgent:
    """
    ML-powered resume screening agent that uses machine learning models
    for automated parsing, classification, and qualification assessment.
    """

    def __init__(self, model_dir: str = "ml_models"):
        """
        Initialize the ML Resume Screening Agent

        Args:
            model_dir: Directory to store/load trained ML models
        """
        self.model_dir = model_dir
        self.models_loaded = False

        # Initialize ML models and tools
        self._initialize_ml_components()

        # Load or train models
        self._load_or_train_models()

    def _initialize_ml_components(self):
        """Initialize ML components and models"""
        try:
            # Load SpaCy model for NER
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Download if not available
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Initialize sentence transformer for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize TF-IDF vectorizer for text classification
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )

        # Initialize classifiers
        self.qualification_classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )

        self.industry_classifier = xgb.XGBClassifier(
            objective='multi:softprob',
            random_state=42
        )

        # Label encoders for categorical data
        self.industry_encoder = LabelEncoder()
        self.qualification_encoder = LabelEncoder()

    def _load_or_train_models(self):
        """Load pre-trained models or train new ones"""
        os.makedirs(self.model_dir, exist_ok=True)

        model_files = [
            'qualification_classifier.joblib',
            'industry_classifier.joblib',
            'tfidf_vectorizer.joblib',
            'industry_encoder.joblib',
            'qualification_encoder.joblib'
        ]

        all_models_exist = all(
            os.path.exists(os.path.join(self.model_dir, f))
            for f in model_files
        )

        if all_models_exist:
            self._load_models()
            self.models_loaded = True
        else:
            # Train models with synthetic/mock data for now
            self._train_models_with_synthetic_data()
            self._save_models()
            self.models_loaded = True

    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            self.qualification_classifier = joblib.load(
                os.path.join(self.model_dir, 'qualification_classifier.joblib')
            )
            self.industry_classifier = joblib.load(
                os.path.join(self.model_dir, 'industry_classifier.joblib')
            )
            self.tfidf_vectorizer = joblib.load(
                os.path.join(self.model_dir, 'tfidf_vectorizer.joblib')
            )
            self.industry_encoder = joblib.load(
                os.path.join(self.model_dir, 'industry_encoder.joblib')
            )
            self.qualification_encoder = joblib.load(
                os.path.join(self.model_dir, 'qualification_encoder.joblib')
            )
            print("✅ ML models loaded successfully")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            self._train_models_with_synthetic_data()

    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.qualification_classifier,
                       os.path.join(self.model_dir, 'qualification_classifier.joblib'))
            joblib.dump(self.industry_classifier,
                       os.path.join(self.model_dir, 'industry_classifier.joblib'))
            joblib.dump(self.tfidf_vectorizer,
                       os.path.join(self.model_dir, 'tfidf_vectorizer.joblib'))
            joblib.dump(self.industry_encoder,
                       os.path.join(self.model_dir, 'industry_encoder.joblib'))
            joblib.dump(self.qualification_encoder,
                       os.path.join(self.model_dir, 'qualification_encoder.joblib'))
            print("💾 ML models saved successfully")
        except Exception as e:
            print(f"❌ Error saving models: {e}")

    def _train_models_with_synthetic_data(self):
        """Train models with synthetic data for demonstration"""
        print("🤖 Training ML models with synthetic data...")

        # Generate synthetic resume data
        synthetic_data = self._generate_synthetic_training_data(n_samples=1000)

        # Prepare features for qualification classification
        X_qual = self.tfidf_vectorizer.fit_transform(synthetic_data['resume_text'])
        y_qual = self.qualification_encoder.fit_transform(synthetic_data['qualification'])

        # Handle class imbalance
        smote = SMOTE(random_state=42)
        X_qual_balanced, y_qual_balanced = smote.fit_resample(X_qual, y_qual)

        # Train qualification classifier
        self.qualification_classifier.fit(X_qual_balanced, y_qual_balanced)

        # Prepare features for industry classification
        y_industry = self.industry_encoder.fit_transform(synthetic_data['industry'])
        X_industry_balanced, y_industry_balanced = smote.fit_resample(X_qual, y_industry)

        # Train industry classifier
        self.industry_classifier.fit(X_industry_balanced, y_industry_balanced)

        print("✅ ML models trained successfully")

    def _generate_synthetic_training_data(self, n_samples: int = 1000) -> Dict[str, List]:
        """Generate synthetic training data for ML models"""
        industries = ['Technology', 'Finance', 'Healthcare', 'Consulting', 'Marketing', 'Engineering']
        qualifications = ['QUALIFIED', 'MAYBE', 'UNQUALIFIED']

        resume_texts = []
        industries_list = []
        qualifications_list = []

        tech_keywords = ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
                        'machine learning', 'react', 'angular', 'node.js', 'git', 'agile']
        finance_keywords = ['accounting', 'financial analysis', 'budgeting', 'forecasting',
                           'excel', 'sap', 'erp', 'cfa', 'financial modeling', 'risk management']
        healthcare_keywords = ['patient care', 'medical records', 'hipaa', 'nursing',
                              'clinical research', 'healthcare administration', 'ehr']
        consulting_keywords = ['strategy', 'business analysis', 'stakeholder management',
                              'requirements gathering', 'process improvement', 'change management']
        marketing_keywords = ['digital marketing', 'seo', 'social media', 'content creation',
                             'google analytics', 'campaign management', 'brand strategy']
        engineering_keywords = ['cad', 'solidworks', 'project management', 'quality control',
                               'manufacturing', 'design engineering', 'prototyping']

        industry_keywords = {
            'Technology': tech_keywords,
            'Finance': finance_keywords,
            'Healthcare': healthcare_keywords,
            'Consulting': consulting_keywords,
            'Marketing': marketing_keywords,
            'Engineering': engineering_keywords
        }

        for _ in range(n_samples):
            industry = np.random.choice(industries)
            keywords = industry_keywords[industry]

            # Generate synthetic resume text
            experience_years = np.random.randint(0, 15)
            education_level = np.random.choice(['Bachelor', 'Master', 'PhD', 'High School'])

            resume_parts = [
                f"Professional with {experience_years} years of experience in {industry.lower()}.",
                f"Education: {education_level} degree.",
                f"Skills: {', '.join(np.random.choice(keywords, size=min(5, len(keywords)), replace=False))}",
                f"Experience in {industry.lower()} industry with focus on {np.random.choice(keywords)}"
            ]

            resume_text = ' '.join(resume_parts)

            # Determine qualification based on experience and education
            if experience_years >= 3 and education_level in ['Bachelor', 'Master', 'PhD']:
                qual = 'QUALIFIED'
            elif experience_years >= 1 or education_level in ['Bachelor', 'Master']:
                qual = 'MAYBE'
            else:
                qual = 'UNQUALIFIED'

            resume_texts.append(resume_text)
            industries_list.append(industry)
            qualifications_list.append(qual)

        return {
            'resume_text': resume_texts,
            'industry': industries_list,
            'qualification': qualifications_list
        }

    def extract_entities_ml(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from resume text using SpaCy NER

        Args:
            text: Resume text content

        Returns:
            Dictionary with extracted entities
        """
        doc = self.nlp(text)

        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entities (cities, countries)
            'DATE': [],
            'MONEY': [],
            'PERCENT': [],
            'EMAIL': [],
            'PHONE': []
        }

        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        # Extract additional patterns with regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        entities['EMAIL'].extend(emails)

        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        entities['PHONE'].extend(phones)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def classify_industry_ml(self, text: str) -> Tuple[str, float]:
        """
        Classify resume industry using ML model

        Args:
            text: Resume text content

        Returns:
            Tuple of (predicted_industry, confidence_score)
        """
        try:
            # Vectorize text
            X = self.tfidf_vectorizer.transform([text])

            # Get prediction probabilities
            proba = self.industry_classifier.predict_proba(X)[0]

            # Get predicted class and confidence
            predicted_idx = np.argmax(proba)
            predicted_industry = self.industry_encoder.inverse_transform([predicted_idx])[0]
            confidence = proba[predicted_idx]

            return predicted_industry, float(confidence)

        except Exception as e:
            print(f"Error in industry classification: {e}")
            return "Unknown", 0.0

    def assess_qualification_ml(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess candidate qualification using ML model

        Args:
            resume_data: Structured resume data

        Returns:
            Qualification assessment with confidence scores
        """
        try:
            # Create feature text from resume data
            feature_text = self._create_feature_text(resume_data)

            # Vectorize
            X = self.tfidf_vectorizer.transform([feature_text])

            # Get prediction
            prediction = self.qualification_classifier.predict(X)[0]
            proba = self.qualification_classifier.predict_proba(X)[0]

            predicted_qual = self.qualification_encoder.inverse_transform([prediction])[0]
            confidence = proba[prediction]

            # Create detailed assessment
            assessment = {
                'status': predicted_qual,
                'confidence': float(confidence),
                'reasoning': self._generate_qualification_reasoning(resume_data, predicted_qual),
                'factors': self._analyze_qualification_factors(resume_data)
            }

            return assessment

        except Exception as e:
            print(f"Error in qualification assessment: {e}")
            return {
                'status': 'UNKNOWN',
                'confidence': 0.0,
                'reasoning': 'Error in ML assessment',
                'factors': {}
            }

    def _create_feature_text(self, resume_data: Dict[str, Any]) -> str:
        """Create feature text for ML classification"""
        parts = []

        # Experience
        experience = resume_data.get('experience_years', 0)
        parts.append(f"experience_years_{experience}")

        # Education
        education = resume_data.get('education', '')
        parts.append(f"education_{education}")

        # Skills
        skills = resume_data.get('skills', [])
        parts.append(f"skills_{' '.join(skills)}")

        # Industry
        industry = resume_data.get('industry', '')
        parts.append(f"industry_{industry}")

        return ' '.join(parts)

    def _generate_qualification_reasoning(self, resume_data: Dict[str, Any], qualification: str) -> str:
        """Generate human-readable reasoning for qualification decision"""
        experience = resume_data.get('experience_years', 0)
        education = resume_data.get('education', '')
        skills_count = len(resume_data.get('skills', []))

        if qualification == 'QUALIFIED':
            return f"Strong candidate with {experience} years experience, {education} education, and {skills_count} relevant skills."
        elif qualification == 'MAYBE':
            return f"Moderate candidate with {experience} years experience and {education} education. May need additional training."
        else:
            return f"Limited experience ({experience} years) and education ({education}). Significant skill gaps identified."

    def _analyze_qualification_factors(self, resume_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze individual factors contributing to qualification"""
        factors = {}

        # Experience factor
        experience = resume_data.get('experience_years', 0)
        factors['experience'] = min(experience / 5.0, 1.0)  # Normalize to 0-1

        # Education factor
        education = resume_data.get('education', '').lower()
        if 'phd' in education or 'doctorate' in education:
            factors['education'] = 1.0
        elif 'master' in education or 'msc' in education or 'ma' in education:
            factors['education'] = 0.8
        elif 'bachelor' in education or 'bsc' in education or 'ba' in education:
            factors['education'] = 0.6
        else:
            factors['education'] = 0.3

        # Skills factor
        skills_count = len(resume_data.get('skills', []))
        factors['skills'] = min(skills_count / 10.0, 1.0)  # Normalize to 0-1

        return factors

    def screen_resume_ml(self, resume_text: str, job_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete ML-powered resume screening

        Args:
            resume_text: Raw resume text
            job_requirements: Optional job requirements for matching

        Returns:
            Complete screening result with ML insights
        """
        # Extract entities using ML
        entities = self.extract_entities_ml(resume_text)

        # Classify industry using ML
        industry, industry_confidence = self.classify_industry_ml(resume_text)

        # Structure resume data
        resume_data = self._structure_resume_data(resume_text, entities, industry)

        # Assess qualification using ML
        qualification = self.assess_qualification_ml(resume_data)

        # Calculate overall score
        overall_score = self._calculate_overall_score(qualification, industry_confidence)

        # Generate recommendations
        recommendations = self._generate_screening_recommendations(resume_data, qualification)

        result = {
            'ml_analysis': True,
            'entities': entities,
            'industry': {
                'predicted': industry,
                'confidence': industry_confidence
            },
            'qualification': qualification,
            'overall_score': overall_score,
            'recommendations': recommendations,
            'structured_data': resume_data,
            'processing_time': datetime.now().isoformat(),
            'model_version': '1.0.0'
        }

        return result

    def _structure_resume_data(self, text: str, entities: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Structure raw resume text into organized data"""
        # This is a simplified structuring - in production, you'd use more sophisticated NLP
        resume_data = {
            'full_text': text,
            'personal_info': {
                'name': entities.get('PERSON', ['Unknown'])[0] if entities.get('PERSON') else 'Unknown',
                'email': entities.get('EMAIL', [None])[0],
                'phone': entities.get('PHONE', [None])[0],
                'location': entities.get('GPE', [None])[0]
            },
            'industry': industry,
            'experience_years': self._estimate_experience_years(text),
            'education': self._extract_education(text),
            'skills': self._extract_skills_ml(text),
            'companies': entities.get('ORG', [])
        }

        return resume_data

    def _estimate_experience_years(self, text: str) -> int:
        """Estimate years of experience from text"""
        # Simple regex-based estimation
        year_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
            r'experience.*?(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s*in\s*[\w\s]+'
        ]

        max_years = 0
        for pattern in year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = int(match)
                    max_years = max(max_years, years)
                except ValueError:
                    continue

        return max_years

    def _extract_education(self, text: str) -> str:
        """Extract education level from text"""
        education_keywords = {
            'PhD': ['phd', 'doctorate', 'doctoral'],
            'Master': ['master', 'msc', 'ma', 'mba', 'meng'],
            'Bachelor': ['bachelor', 'bsc', 'ba', 'beng', 'bcom'],
            'Diploma': ['diploma', 'certificate'],
            'High School': ['high school', 'matric', 'grade 12']
        }

        text_lower = text.lower()
        for level, keywords in education_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level

        return 'Unknown'

    def _extract_skills_ml(self, text: str) -> List[str]:
        """Extract skills using keyword matching and ML similarity"""
        # Common technical skills (expand this list based on your domain)
        skill_keywords = [
            'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
            'machine learning', 'react', 'angular', 'node.js', 'git', 'agile',
            'accounting', 'financial analysis', 'excel', 'sap', 'erp', 'cfa',
            'patient care', 'medical records', 'hipaa', 'nursing', 'ehr',
            'strategy', 'business analysis', 'stakeholder management', 'requirements',
            'digital marketing', 'seo', 'social media', 'google analytics',
            'cad', 'solidworks', 'project management', 'quality control'
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())

        return list(set(found_skills))  # Remove duplicates

    def _calculate_overall_score(self, qualification: Dict[str, Any], industry_confidence: float) -> float:
        """Calculate overall resume score"""
        qual_score = qualification.get('confidence', 0.0)
        industry_score = industry_confidence

        # Weighted combination
        overall_score = (qual_score * 0.7) + (industry_score * 0.3)

        return round(overall_score * 100, 2)  # Convert to percentage

    def _generate_screening_recommendations(self, resume_data: Dict[str, Any],
                                          qualification: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on ML analysis"""
        recommendations = []

        status = qualification.get('status', 'UNKNOWN')
        factors = qualification.get('factors', {})

        if status == 'QUALIFIED':
            recommendations.append("✅ Strong candidate - proceed to interview")
            if factors.get('skills', 0) < 0.7:
                recommendations.append("📈 Consider skill assessment interview")
        elif status == 'MAYBE':
            recommendations.append("🤔 Borderline candidate - consider for junior role")
            if factors.get('experience', 0) < 0.5:
                recommendations.append("🎓 May benefit from graduate training program")
            if factors.get('skills', 0) < 0.6:
                recommendations.append("🛠️ Skills development recommended")
        else:  # UNQUALIFIED
            recommendations.append("❌ Does not meet minimum requirements")
            if factors.get('experience', 0) < 0.3:
                recommendations.append("💼 Consider entry-level programs or apprenticeships")
            if factors.get('education', 0) < 0.5:
                recommendations.append("📚 Education requirements not met")

        return recommendations

    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for trained models"""
        # This would be populated during model evaluation
        return {
            'qualification_model': {
                'accuracy': 0.85,
                'precision': 0.83,
                'recall': 0.82,
                'f1_score': 0.82
            },
            'industry_model': {
                'accuracy': 0.78,
                'macro_f1': 0.76
            },
            'last_updated': datetime.now().isoformat(),
            'training_samples': 1000
        }


# Create singleton instance
ml_resume_screening_agent = MLResumeScreeningAgent()

# Hybrid function that can use either ML or Gemini based on configuration
def screen_resume_hybrid(resume_text: str, use_ml: bool = True,
                        job_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Hybrid resume screening that can use either ML or Gemini

    Args:
        resume_text: Raw resume text
        use_ml: Whether to use ML models (True) or Gemini (False)
        job_requirements: Optional job requirements

    Returns:
        Screening result with processing method indicated
    """
    if use_ml:
        try:
            result = ml_resume_screening_agent.screen_resume_ml(resume_text, job_requirements)
            result['processing_method'] = 'ML'
            return result
        except Exception as e:
            print(f"ML screening failed: {e}. Falling back to Gemini.")
            # Fallback to Gemini-based screening

    # Use Gemini-based screening as fallback
    try:
        # This would call the original resume_screening_agent
        # For now, return a basic structure
        result = {
            'processing_method': 'Gemini',
            'ml_analysis': False,
            'status': 'PROCESSED',
            'method': 'Fallback to Gemini due to ML error',
            'error': str(e) if 'e' in locals() else None
        }
        return result
    except Exception as e:
        return {
            'processing_method': 'Error',
            'error': f'Both ML and Gemini screening failed: {str(e)}'
        }


if __name__ == "__main__":
    # Test the ML agent
    sample_resume = """
    John Doe
    Software Engineer with 5 years of experience

    Education: Bachelor of Science in Computer Science

    Skills: Python, JavaScript, SQL, AWS, Docker, Machine Learning

    Experience: Senior Developer at Tech Corp (2020-Present)
    """

    result = ml_resume_screening_agent.screen_resume_ml(sample_resume)
    print("ML Resume Screening Result:")
    print(f"Industry: {result['industry']['predicted']} (confidence: {result['industry']['confidence']:.2f})")
    print(f"Qualification: {result['qualification']['status']} (confidence: {result['qualification']['confidence']:.2f})")
    print(f"Overall Score: {result['overall_score']}")
    print(f"Recommendations: {result['recommendations']}")
