"""
Database utilities for job storage and retrieval
"""

import chromadb
import google.genai as genai
import os
from .scraping import extract_skills_from_description

# Vector Database for job postings
chroma_client = chromadb.Client()

# Check if collection exists, create or get it
try:
    jobs_collection = chroma_client.get_collection(name="job_postings")
except:
    jobs_collection = chroma_client.create_collection(
        name="job_postings",
        metadata={"hnsw:space": "cosine"}
    )

# Initialize Gemini client for embeddings
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def store_jobs_in_db(jobs):
    """
    Store scraped jobs in ChromaDB
    """
    for job in jobs:
        try:
            # Generate unique ID if not present
            job_id = job.get('id', f"{job['source']}_{hash(job['url'])}")

            # Extract skills from job description
            description = job.get('description', f"{job['title']} at {job['company']} in {job['location']}")
            required_skills = extract_skills_from_description(description)

            # Create embedding from available information
            embedding_text = f"{job['title']} {job['company']} {job['location']} {description} {' '.join(required_skills)}"

            response = client.models.embed_content(
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
        except Exception as e:
            print(f"Error storing job {job.get('title', 'unknown')}: {e}")
