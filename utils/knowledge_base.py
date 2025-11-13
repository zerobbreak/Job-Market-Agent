"""
Knowledge Base System
Comprehensive vector embeddings for job market intelligence
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import chromadb

# Import ChromaDB client
from utils.database import chroma_client

# Setup logger
logger = logging.getLogger('job_market_analyzer.knowledge_base')

# Lazy-initialize Gemini client to avoid requiring API key at import time
genai_client = None

def get_genai_client():
    """Get Google GenAI client (lazy initialization)"""
    # Short-circuit in OpenRouter-only mode
    if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
        raise RuntimeError("OpenRouter-only mode enabled; Google GenAI disabled")
    global genai_client
    if genai_client is None:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        genai_client = genai
    return genai_client

class KnowledgeBase:
    """
    Comprehensive knowledge base with vector embeddings for job market intelligence
    """
    def __init__(self):
        """
        Initialize the Knowledge Base system
        """
        self.collections = {}
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

        # Initialize collections
        self._initialize_collections()

    def _initialize_collections(self):
        """Initialize ChromaDB collections for each knowledge source"""
        for source_name in self.knowledge_sources.keys():
            try:
                # Try to get existing collection
                collection = chroma_client.get_collection(name=source_name)
                self.collections[source_name] = collection
                logger.info(f"Loaded existing collection: {source_name}")
            except chromadb.errors.NotFoundError:
                # Create new collection if it doesn't exist
                collection = chroma_client.create_collection(name=source_name)
                self.collections[source_name] = collection
                logger.info(f"Created new collection: {source_name}")
            except Exception as e:
                logger.error(f"Error initializing collection {source_name}: {e}", exc_info=True)
                raise

    def add_document(self, source: str, document: Dict[str, Any]) -> bool:
        """
        Add a document to the knowledge base with vector embedding

        Args:
            source: Knowledge source name (e.g., 'job_descriptions')
            document: Dict with 'text', 'metadata', 'id' keys
        """
        if source not in self.collections:
            logger.error(f"Unknown knowledge source: {source}")
            return False

        try:
            # Clean metadata - convert lists to strings for ChromaDB compatibility
            cleaned_metadata = {}
            for key, value in document['metadata'].items():
                if isinstance(value, list):
                    cleaned_metadata[key] = ', '.join(str(item) for item in value)
                else:
                    cleaned_metadata[key] = value

            # Add to collection
            collection = self.collections[source]
            
            # Check if OpenRouter-only mode is enabled
            if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
                # Add without embeddings - ChromaDB will use default embeddings
                collection.add(
                    documents=[document['text']],
                    metadatas=[cleaned_metadata],
                    ids=[document['id']]
                )
            else:
                # Generate embedding using Google GenAI
                try:
                    genai = get_genai_client()
                    embedding = genai.embed_content(
                        model="models/text-embedding-004",
                        content=document['text'],
                        task_type="retrieval_document"
                    )
                    collection.add(
                        embeddings=[embedding['embedding']],
                        documents=[document['text']],
                        metadatas=[cleaned_metadata],
                        ids=[document['id']]
                    )
                except RuntimeError as e:
                    # Fallback: add without embeddings if GenAI is disabled
                    collection.add(
                        documents=[document['text']],
                        metadatas=[cleaned_metadata],
                        ids=[document['id']]
                    )

            logger.info(f"Added document {document['id']} to {source}")
            return True

        except Exception as e:
            logger.error(f"Error adding document to {source}: {e}", exc_info=True)
            return False

    def search_similar(self, source: str, query: str, n_results: int = 5) -> Optional[Dict]:
        """
        Search for similar documents using vector similarity

        Args:
            source: Knowledge source to search
            query: Search query
            n_results: Number of results to return
        """
        if source not in self.collections:
            logger.error(f"Unknown knowledge source: {source}")
            return None

        try:
            # Search collection
            collection = self.collections[source]
            
            # Check if OpenRouter-only mode is enabled
            if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
                # Use text-based search (ChromaDB will handle it)
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            else:
                # Generate query embedding using Google GenAI
                try:
                    genai = get_genai_client()
                    query_embedding = genai.embed_content(
                        model="models/text-embedding-004",
                        content=query,
                        task_type="retrieval_query"
                    )
                    results = collection.query(
                        query_embeddings=[query_embedding['embedding']],
                        n_results=n_results
                    )
                except RuntimeError:
                    # Fallback: use text-based search if GenAI is disabled
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results
                    )

            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }

        except Exception as e:
            logger.error(f"Error searching {source}: {e}", exc_info=True)
            return None

    def get_collection_stats(self, source: str) -> Optional[Dict]:
        """Get statistics for a knowledge source collection"""
        if source not in self.collections:
            return None

        try:
            collection = self.collections[source]
            count = collection.count()

            return {
                'source': source,
                'document_count': count,
                'description': self.knowledge_sources[source]['description'],
                'metadata': self.knowledge_sources[source]
            }
        except Exception as e:
            logger.error(f"Error getting stats for {source}: {e}", exc_info=True)
            return None

    def get_all_stats(self) -> Dict:
        """Get statistics for all knowledge sources"""
        stats = {}
        for source in self.knowledge_sources.keys():
            stats[source] = self.get_collection_stats(source)
        return stats

    def initialize_sample_data(self):
        """Initialize collections with sample data for demonstration"""
        logger.info("Initializing knowledge base with sample data...")

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
            logger.info(f"Adding {len(documents)} documents to {source}...")
            for doc in documents:
                if self.add_document(source, doc):
                    total_added += 1
                time.sleep(0.1)  # Rate limiting

        logger.info(f"Added {total_added} sample documents to knowledge base")
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
            if source in self.collections:
                results = self.search_similar(source, query, n_results)
                if results and results['documents']:
                    context[source] = results

        return context

# Global knowledge base instance
knowledge_base = KnowledgeBase()
