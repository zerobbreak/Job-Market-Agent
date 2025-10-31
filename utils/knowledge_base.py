"""
Knowledge Base System
Comprehensive vector embeddings for job market intelligence
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai

# ChromaDB import removed - using simplified knowledge base without vector storage

class KnowledgeBase:
    """
    Comprehensive knowledge base with vector embeddings for job market intelligence
    """
    def __init__(self):
        """
        Initialize the Knowledge Base system
        """
        self.knowledge_sources = {
            'job_descriptions': {
                'source': 'PNet, CareerJunction, LinkedIn',
                'size': '50,000+ SA job postings',
                'categories': ['IT', 'Finance', 'Marketing', 'Engineering', 'Healthcare'],
                'description': 'South African job postings with detailed requirements and descriptions'
            },
            'successful_cvs': {
                'source': 'Anonymized graduate CVs',
                'size': '10,000+ examples',
                'features': 'Hired within 6 months of graduation',
                'description': 'Successful graduate CVs that led to job offers'
            },
            'interview_questions': {
                'source': 'Glassdoor, company websites, student surveys',
                'size': '5,000+ questions by industry',
                'description': 'Real interview questions asked by South African companies'
            },
            'skills_taxonomy': {
                'source': 'O*NET, LinkedIn Skills Graph',
                'size': '20,000+ skills with relationships',
                'description': 'Skills taxonomy with relationships and importance levels'
            },
            'sa_context': {
                'source': 'Stats SA, World Bank, local research',
                'data': 'Youth unemployment stats, transport costs, salary ranges',
                'description': 'South African employment context and market data'
            }
        }

        # Initialize in-memory storage instead of ChromaDB
        self.documents = {source: [] for source in self.knowledge_sources.keys()}
        print("[KB] Knowledge base initialized (simplified mode without vector storage)")

    # _initialize_collections method removed - using simplified storage

    def add_document(self, source: str, document: Dict[str, Any]) -> bool:
        """
        Add a document to the knowledge base (simplified without embeddings)

        Args:
            source: Knowledge source name (e.g., 'job_descriptions')
            document: Dict with 'text', 'metadata', 'id' keys
        """
        if source not in self.documents:
            print(f"[ERROR] Unknown knowledge source: {source}")
            return False

        try:
            # Clean metadata - convert lists to strings for compatibility
            cleaned_metadata = {}
            for key, value in document['metadata'].items():
                if isinstance(value, list):
                    cleaned_metadata[key] = ', '.join(str(item) for item in value)
                else:
                    cleaned_metadata[key] = value

            # Add to in-memory storage (no embedding generation)
            doc_entry = {
                'id': document['id'],
                'text': document['text'],
                'metadata': cleaned_metadata,
                'added_at': datetime.now().isoformat(),
                'word_count': len(document['text'].split())
            }

            self.documents[source].append(doc_entry)

            print(f"[OK] Added document {document['id']} to {source}")
            return True

        except Exception as e:
            print(f"[ERROR] Error adding document to {source}: {e}")
            return False

    def search_similar(self, source: str, query: str, n_results: int = 5) -> Optional[Dict]:
        """
        Search for similar documents using simple text matching (no vectors)

        Args:
            source: Knowledge source to search
            query: Search query
            n_results: Number of results to return
        """
        if source not in self.documents:
            print(f"[ERROR] Unknown knowledge source: {source}")
            return None

        try:
            # Simple text search (case-insensitive)
            query_lower = query.lower()
            matching_docs = []

            for doc in self.documents[source]:
                text_lower = doc['text'].lower()
                if query_lower in text_lower:
                    # Calculate simple relevance score (number of query words found)
                    query_words = set(query_lower.split())
                    text_words = set(text_lower.split())
                    common_words = query_words.intersection(text_words)
                    relevance_score = len(common_words) / len(query_words) if query_words else 0

                    matching_docs.append({
                        'id': doc['id'],
                        'text': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
                        'metadata': doc['metadata'],
                        'relevance_score': relevance_score
                    })

            # Sort by relevance and return top results
            matching_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
            top_results = matching_docs[:n_results]

            return {
                'query': query,
                'source': source,
                'results': top_results,
                'total_found': len(top_results)
            }

        except Exception as e:
            print(f"[ERROR] Error searching {source}: {e}")
            return None

    def get_collection_stats(self, source: str) -> Optional[Dict]:
        """Get statistics for a knowledge source (simplified)"""
        if source not in self.documents:
            return None

        try:
            doc_count = len(self.documents[source])
            total_words = sum(doc.get('word_count', 0) for doc in self.documents[source])

            return {
                'source': source,
                'document_count': doc_count,
                'total_words': total_words,
                'description': self.knowledge_sources[source]['description'],
                'metadata': self.knowledge_sources[source]
            }
        except Exception as e:
            print(f"[ERROR] Error getting stats for {source}: {e}")
            return None

    def get_all_stats(self) -> Dict:
        """Get statistics for all knowledge sources"""
        stats = {}
        for source in self.knowledge_sources.keys():
            stats[source] = self.get_collection_stats(source)
        return stats

    def initialize_sample_data(self):
        """Initialize collections with sample data for demonstration"""
        print("[KB] Initializing knowledge base with sample data...")

        # Sample job descriptions
        job_samples = [
            {
                'id': 'job_001',
                'text': 'Senior Software Engineer - Full Stack Developer required with 3+ years experience in React, Node.js, and Python. Must have experience with cloud platforms (AWS/Azure) and database design. Competitive salary + benefits.',
                'metadata': {
                    'category': 'IT',
                    'company': 'TechCorp SA',
                    'location': 'Johannesburg',
                    'salary_range': 'R35,000 - R55,000',
                    'required_skills': ['React', 'Node.js', 'Python', 'AWS'],
                    'date_posted': datetime.now().isoformat()
                }
            },
            {
                'id': 'job_002',
                'text': 'Junior Data Analyst - Entry level position requiring Excel proficiency and basic SQL knowledge. Python/R knowledge advantageous. Great opportunity for recent graduates.',
                'metadata': {
                    'category': 'IT',
                    'company': 'Data Insights Pty Ltd',
                    'location': 'Cape Town',
                    'salary_range': 'R18,000 - R25,000',
                    'required_skills': ['Excel', 'SQL', 'Python'],
                    'date_posted': datetime.now().isoformat()
                }
            }
        ]

        # Sample successful CVs
        cv_samples = [
            {
                'id': 'cv_001',
                'text': 'Computer Science Graduate with distinction. Skills: Python, Java, React, Node.js. Projects: Instagram clone (React/Node), E-commerce platform (Django). Work experience: Tutoring assistant. Leadership: Student council member.',
                'metadata': {
                    'degree': 'Computer Science',
                    'grade': 'Distinction',
                    'time_to_hire': '3 months',
                    'final_role': 'Junior Developer',
                    'key_skills': ['Python', 'React', 'Node.js'],
                    'projects_count': 2
                }
            }
        ]

        # Sample interview questions
        question_samples = [
            {
                'id': 'q_001',
                'text': 'Tell me about a time when you had to learn a new technology quickly. What was your approach?',
                'metadata': {
                    'category': 'Technical',
                    'industry': 'IT',
                    'difficulty': 'Medium',
                    'common_answer': 'STAR method with specific example'
                }
            },
            {
                'id': 'q_002',
                'text': 'Why do you want to work for our company in South Africa specifically?',
                'metadata': {
                    'category': 'Behavioral',
                    'industry': 'All',
                    'difficulty': 'Easy',
                    'sa_context': True
                }
            }
        ]

        # Sample skills taxonomy
        skill_samples = [
            {
                'id': 'skill_001',
                'text': 'Python Programming: Object-oriented programming, data structures, algorithms, web frameworks (Django/Flask), data analysis (Pandas/NumPy)',
                'metadata': {
                    'skill_category': 'Programming Languages',
                    'importance': 'High',
                    'related_skills': ['Java', 'JavaScript', 'SQL'],
                    'industry_focus': ['IT', 'Finance', 'Data Science']
                }
            }
        ]

        # Sample SA context with youth unemployment focus
        sa_samples = [
            {
                'id': 'sa_001',
                'text': 'South African youth unemployment rate: 45.5% (Q4 2023). Graduate unemployment: 35%. Average time to first job: 8.2 months. Transport costs in major cities: 15-25% of salary. Entry-level salaries: R8,000-R15,000/month.',
                'metadata': {
                    'data_type': 'Employment Statistics',
                    'region': 'South Africa',
                    'source': 'Stats SA',
                    'last_updated': '2024-01',
                    'key_insights': ['High competition', 'Transport important', 'Networking crucial', 'Realistic salary expectations']
                }
            },
            {
                'id': 'sa_transport',
                'text': 'Transport costs in South Africa: Johannesburg CBD commute R800-1,500/month. Cape Town minibus taxis R400-800/month. Pretoria bus/train R300-600/month. 70% of youth cannot afford reliable transport to work.',
                'metadata': {
                    'data_type': 'Transport Economics',
                    'region': 'Major Cities',
                    'source': 'World Bank, Local Research',
                    'key_insights': ['High transport costs', 'Reliability issues', 'Prioritize remote/nearby jobs']
                }
            },
            {
                'id': 'sa_learnerships',
                'text': 'SETA Learnership Programs: Banking SETA (R3,500/month), Services SETA (R3,000/month), Manufacturing SETA (R4,000/month). YES Initiative: Youth Employment Service provides subsidized employment for graduates under 35.',
                'metadata': {
                    'data_type': 'Skills Development',
                    'region': 'South Africa',
                    'source': 'Department of Higher Education, YES Initiative',
                    'key_insights': ['Paid training', 'Work experience', 'Government subsidized', 'Entry point for graduates']
                }
            },
            {
                'id': 'sa_internships',
                'text': 'Graduate Internship Programs: Standard Bank YES (R8,000-12,000/month), Nedbank YES (R7,000-10,000/month), Government internships (R6,000-8,000/month). 12-24 month duration with permanent placement potential.',
                'metadata': {
                    'data_type': 'Graduate Programs',
                    'region': 'South Africa',
                    'source': 'Banking Association, Government Programs',
                    'key_insights': ['Structured development', 'Market salary', 'Career progression', 'Permanent placement']
                }
            },
            {
                'id': 'sa_languages',
                'text': 'South African workplace languages: English (universal), Afrikaans (Western Cape, Northern Cape), Zulu (KZN, Gauteng), Xhosa (Eastern Cape, Western Cape), Sotho (Free State, Gauteng). Code-switching common.',
                'metadata': {
                    'data_type': 'Language Requirements',
                    'region': 'South Africa',
                    'source': 'Language Policy Framework',
                    'key_insights': ['Multilingual workplace', 'Cultural competence', 'Communication skills']
                }
            },
            {
                'id': 'sa_remote_work',
                'text': 'Remote work adoption: 35% of South African companies offer hybrid/remote options. Tech sector leads with 60% remote-capable. Transport savings: R500-1,000/month for remote workers.',
                'metadata': {
                    'data_type': 'Work Arrangements',
                    'region': 'South Africa',
                    'source': 'World Economic Forum, Local Surveys',
                    'key_insights': ['Remote work growing', 'Transport savings', 'Work-life balance', 'Digital skills needed']
                }
            }
        ]

        # Add sample data to collections
        sample_data = {
            'job_descriptions': job_samples,
            'successful_cvs': cv_samples,
            'interview_questions': question_samples,
            'skills_taxonomy': skill_samples,
            'sa_context': sa_samples
        }

        total_added = 0
        for source, documents in sample_data.items():
            print(f"[ADD] Adding {len(documents)} documents to {source}...")
            for doc in documents:
                if self.add_document(source, doc):
                    total_added += 1
                time.sleep(0.1)  # Rate limiting

        print(f"[OK] Added {total_added} sample documents to knowledge base")
        return total_added

    def retrieve_context(self, query: str, sources: List[str] = None, n_results: int = 3) -> Dict:
        """
        Retrieve relevant context from multiple knowledge sources

        Args:
            query: Search query
            sources: List of sources to search (default: all)
            n_results: Number of results per source
        """
        if sources is None:
            sources = list(self.knowledge_sources.keys())

        context = {}
        for source in sources:
            if source in self.documents:
                results = self.search_similar(source, query, n_results)
                if results and results.get('results'):
                    context[source] = results

        return context

# Global knowledge base instance
knowledge_base = KnowledgeBase()
