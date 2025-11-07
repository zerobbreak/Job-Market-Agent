"""
Database utilities for job storage and retrieval
"""

import chromadb
import google.genai as genai
import os
import logging
from typing import List, Dict, Any
from .scraping import extract_skills_from_description

# Setup logger
logger = logging.getLogger('job_market_analyzer.database')

# Vector Database for job postings
chroma_client = chromadb.Client()

# Check if collection exists, create or get it
try:
    jobs_collection = chroma_client.get_collection(name="job_postings")
    logger.debug("Loaded existing job_postings collection")
except chromadb.errors.NotFoundError:
    jobs_collection = chroma_client.create_collection(
        name="job_postings",
        metadata={"hnsw:space": "cosine"}
    )
    logger.info("Created new job_postings collection")
except Exception as e:
    logger.error(f"Error accessing ChromaDB collection: {e}", exc_info=True)
    raise

# Lazy-initialize Gemini client for embeddings
client = None


def get_client():
    # Disable Google client in OpenRouter-only mode
    if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
        raise RuntimeError("OpenRouter-only mode enabled; Google GenAI disabled")
    global client
    if client is None:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        client = genai.Client(api_key=api_key)
    return client


def store_jobs_in_db(jobs: List[Dict[str, Any]]) -> int:
    """
    Store scraped jobs in ChromaDB
    
    Args:
        jobs: List of job dictionaries to store
        
    Returns:
        Number of jobs successfully stored
    """
    stored_count = 0
    for job in jobs:
        try:
            # Generate unique ID if not present
            job_id = job.get('id', f"{job['source']}_{hash(job['url'])}")

            # Extract skills from job description
            description = job.get('description', f"{job['title']} at {job['company']} in {job['location']}")
            required_skills = extract_skills_from_description(description)

            # Create embedding from available information
            embedding_text = f"{job['title']} {job['company']} {job['location']} {description} {' '.join(required_skills)}"

            if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
                # Store metadata without embeddings when OpenRouter-only
                jobs_collection.add(
                    ids=[job_id],
                    metadatas=[{
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'description': description,
                        'url': job['url'],
                        'source': job['source'],
                        'required_skills': ', '.join(required_skills),
                        'posted_date': job.get('posted_date', __import__('datetime').datetime.now().isoformat())
                    }],
                    documents=[description]
                )
                stored_count += 1
                logger.debug(f"Stored job: {job.get('title', 'unknown')} (ID: {job_id})")
            else:
                response = get_client().models.embed_content(
                    model="text-embedding-004",
                    contents=embedding_text
                )
                embedding = response.embeddings[0].values

                # Add to ChromaDB
                jobs_collection.add(
                    ids=[job_id],
                    embeddings=[embedding],
                    metadatas=[{
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'description': description,
                        'url': job['url'],
                        'source': job['source'],
                        'required_skills': ', '.join(required_skills),
                        'posted_date': job.get('posted_date', __import__('datetime').datetime.now().isoformat())
                    }],
                    documents=[description]
                )
                stored_count += 1
                logger.debug(f"Stored job with embedding: {job.get('title', 'unknown')} (ID: {job_id})")
        except Exception as e:
            logger.error(f"Error storing job {job.get('title', 'unknown')}: {e}", exc_info=True)
    
    logger.info(f"Successfully stored {stored_count}/{len(jobs)} jobs in database")
    return stored_count
