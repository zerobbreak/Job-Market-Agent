"""
Scraping utilities for job data extraction and processing
"""

import google.genai as genai
import os
from scrapper import scrape_all

# Initialize Gemini client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def extract_skills_from_description(description):
    """
    Extract technical skills from job description using AI
    """
    # Common tech skills to look for
    common_skills = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'NoSQL',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Git', 'Agile', 'Scrum', 'CI/CD'
    ]

    found_skills = []
    description_lower = description.lower()

    for skill in common_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)

    # Use Gemini for more sophisticated extraction
    try:
        extraction_agent = __import__('agents.job_matcher_agent').job_matcher.__class__(
            name="Skill Extractor",
            model=__import__('agno.models.google').Gemini(id="gemini-2.0-flash"),
            instructions="Extract technical skills from job descriptions. Return as comma-separated list."
        )

        result = extraction_agent.run(f"Extract skills from: {description}")
        ai_skills = [s.strip() for s in result.content.split(',')]
        found_skills.extend(ai_skills)

        # Remove duplicates
        found_skills = list(set(found_skills))
    except:
        pass

    return found_skills


def semantic_skill_match(student_skills, required_skills):
    """
    Use word embeddings to handle synonyms and variations
    Example: "JavaScript" matches "JS", "ECMAScript"
    """
    if not student_skills or not required_skills:
        return [], 0

    try:
        # Generate embeddings for student skills
        student_embeddings = []
        for skill in student_skills:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=skill
            )
            student_embeddings.append(response.embeddings[0].values)

        # Generate embeddings for required skills
        required_embeddings = []
        for skill in required_skills:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=skill
            )
            required_embeddings.append(response.embeddings[0].values)

        # Convert to numpy arrays
        import numpy as np
        student_embeddings = np.array(student_embeddings)
        required_embeddings = np.array(required_embeddings)

        # Compute cosine similarity matrix
        # Normalize vectors for cosine similarity
        student_norm = student_embeddings / np.linalg.norm(student_embeddings, axis=1, keepdims=True)
        required_norm = required_embeddings / np.linalg.norm(required_embeddings, axis=1, keepdims=True)
        similarity_matrix = np.dot(student_norm, required_norm.T)

        # For each required skill, find best matching student skill
        matches = []
        for i, req_skill in enumerate(required_skills):
            best_match_idx = np.argmax(similarity_matrix[:, i])
            similarity_score = similarity_matrix[best_match_idx, i]

            if similarity_score > 0.75:  # High similarity threshold
                matches.append({
                    'required': req_skill,
                    'student_has': student_skills[best_match_idx],
                    'confidence': float(similarity_score)
                })

        match_percentage = len(matches) / len(required_skills) * 100
        return matches, match_percentage

    except Exception as e:
        print(f"Error in semantic skill matching: {e}")
        return [], 0


def discover_new_jobs(student_profile, location="Johannesburg", verbose=False):
    """
    Scrape job boards for new opportunities using advanced Playwright-based scraping
    """
    desired_role = student_profile.get('desired_role', 'software engineer')

    if verbose:
        print("🔄 Starting advanced job scraping with Playwright...")
        print(f"   🎯 Searching for: {desired_role} in {location}")

    # Use the advanced scraping from scrapper.py
    all_jobs = scrape_all(desired_role, location)

    if verbose:
        print(f"📊 Scraped {len(all_jobs)} total jobs")

    # Store in ChromaDB
    if all_jobs:
        from .database import store_jobs_in_db
        store_jobs_in_db(all_jobs)
        if verbose:
            print("💾 Jobs stored in database")
    elif verbose:
        print("⚠️ No jobs scraped, skipping database storage")

    # Match against student profile
    from .matching import match_student_to_jobs
    matched_jobs = match_student_to_jobs(student_profile)

    return matched_jobs
