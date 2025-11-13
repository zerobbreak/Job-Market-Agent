"""
Scraping utilities for job data extraction and processing
"""

import google.genai as genai
import os
import logging
from .scrapper import scrape_all_advanced
from tqdm import tqdm

# Setup logger
logger = logging.getLogger('job_market_analyzer.scraping')

# Lazy-initialize Gemini client to avoid requiring API key at import time
client = None


def get_client():
    # Short-circuit in OpenRouter-only mode
    if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
        raise RuntimeError("OpenRouter-only mode enabled; Google GenAI disabled")
    global client
    if client is None:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        client = genai.Client(api_key=api_key)
    return client

# Configuration for API resilience
API_CONFIG = {
    'max_retries': int(os.getenv('API_MAX_RETRIES', '3')),
    'retry_delay_base': float(os.getenv('API_RETRY_DELAY', '2.0')),
    'timeout': int(os.getenv('API_TIMEOUT', '30')),
}


def check_api_status():
    """
    Check if the Gemini API is available and responsive
    Returns: (is_available: bool, status_message: str)
    """
    try:
        # Simple test request to check API availability
        if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
            return False, "API disabled (OpenRouter-only mode)"
        response = get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello",
            config={'max_output_tokens': 10}  # Minimal response
        )
        return True, "API is available"
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            return False, "API is overloaded (503 Service Unavailable)"
        elif "429" in error_msg or "RATE_LIMIT" in error_msg:
            return False, "API rate limit exceeded"
        elif "401" in error_msg or "PERMISSION_DENIED" in error_msg:
            return False, "API authentication failed"
        else:
            return False, f"API error: {error_msg}"


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
        if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
            return found_skills
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
        if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
            return [], 0
        # Generate embeddings for student skills
        student_embeddings = []
        for skill in student_skills:
            response = get_client().models.embed_content(
                model="text-embedding-004",
                contents=skill
            )
            student_embeddings.append(response.embeddings[0].values)

        # Generate embeddings for required skills
        required_embeddings = []
        for skill in required_skills:
            response = get_client().models.embed_content(
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
        logger.error(f"Error in semantic skill matching: {e}", exc_info=True)
        return [], 0


def discover_new_jobs(student_profile, location="Johannesburg", verbose=False, max_jobs=20):
    """
    Scrape job boards for new opportunities using advanced Playwright-based scraping
    """
    # Use multiple search terms if available, otherwise fall back to desired_role
    search_terms = student_profile.get('search_terms', [])
    if not search_terms:
        desired_role = student_profile.get('desired_role', 'software engineer')
        search_terms = [desired_role]

    if verbose:
        logger.info(f"Starting advanced job scraping with search terms: {search_terms}")
        logger.info(f"Location: {location}")

    all_jobs = []

    # Use progress bar for multiple search terms
    if len(search_terms) > 1:
        search_iterator = tqdm(search_terms, desc="🔍 Scraping job sites", unit="search")
    else:
        search_iterator = search_terms

    for search_term in search_iterator:
        if verbose and len(search_terms) == 1:
            logger.info(f"Scraping for: '{search_term}' in {location}")

        # Use the advanced scraping from scrapper.py
        term_jobs = scrape_all_advanced(search_term, location, results_wanted=max_jobs)

        # Add search term info to jobs for tracking
        for job in term_jobs:
            job['searched_with'] = search_term

        all_jobs.extend(term_jobs)

        if verbose and len(search_terms) == 1:
            logger.info(f"Found {len(term_jobs)} jobs for '{search_term}'")
        elif len(search_terms) > 1:
            # Update progress bar description
            search_iterator.set_postfix({"jobs_found": len(term_jobs), "total": len(all_jobs)})

        # Small delay between searches to be respectful
        if len(search_terms) > 1:
            import time
            time.sleep(1)

    # Close progress bar if it was used
    if len(search_terms) > 1:
        search_iterator.close()

    if verbose:
        logger.info(f"Scraped {len(all_jobs)} total jobs")

    # Store in ChromaDB
    if all_jobs:
        from .database import store_jobs_in_db
        stored_count = store_jobs_in_db(all_jobs)
        if verbose:
            logger.info(f"Stored {stored_count} jobs in database")
    elif verbose:
        logger.warning("No jobs scraped, skipping database storage")

    # Match against student profile
    from .matching import match_student_to_jobs
    matched_jobs = match_student_to_jobs(student_profile)

    return matched_jobs


# Extract keywords from job description
def extract_job_keywords(job_description, max_retries=None):
    """
    Use Gemini to identify critical keywords hiring managers look for
    Includes retry logic for handling API overload
    """
    import time
    import random

    # Use configuration values if not specified
    if max_retries is None:
        max_retries = API_CONFIG['max_retries']

    retry_delay_base = API_CONFIG['retry_delay_base']

    for attempt in range(max_retries):
        try:
            if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
                return _extract_keywords_fallback(job_description)
            response = get_client().models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""
                Analyze this job description and extract:

                1. MUST-HAVE KEYWORDS (10-15):
                   - Technical skills (programming languages, tools, methodologies)
                   - Certifications and qualifications
                   - Years of experience
                   - Industry-specific terms

                2. NICE-TO-HAVE KEYWORDS (5-10):
                   - Soft skills (leadership, collaboration)
                   - Preferred qualifications
                   - Domain knowledge

                3. ACTION VERBS (5-10):
                   - Verbs used in job description (develop, manage, analyze)

                4. KEYWORD VARIATIONS:
                   - Synonyms and related terms
                   - Abbreviations (AI = Artificial Intelligence)

                Job Description:
                {job_description}

                Return structured JSON with categorized keywords and importance weights.
                """
            )

            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            error_message = str(e)
            if ("503" in error_message or "UNAVAILABLE" in error_message or
                "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or
                "QUOTA" in error_message.lower()):
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter using configured base
                    wait_time = (retry_delay_base ** attempt) + random.uniform(0, 1)
                    logger.warning(f"API rate limited/overloaded (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("API still rate limited after all retries. Using fallback keyword extraction.")
                    return _extract_keywords_fallback(job_description)
            else:
                # Non-retryable error, don't retry
                logger.error(f"Error extracting job keywords: {e}", exc_info=True)
                return _extract_keywords_fallback(job_description)

    # This should not be reached, but just in case
    return _extract_keywords_fallback(job_description)


def _extract_keywords_fallback(job_description):
    """
    Fallback keyword extraction when API is unavailable
    Uses simple pattern matching and common keywords
    """
    import re

    # Common technical keywords
    common_tech_keywords = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'NoSQL',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Git', 'Agile', 'Scrum', 'CI/CD', 'DevOps'
    ]

    # Common action verbs
    action_verbs = [
        'develop', 'design', 'implement', 'manage', 'analyze', 'create',
        'build', 'maintain', 'optimize', 'deploy', 'test', 'collaborate',
        'lead', 'coordinate', 'integrate', 'automate', 'document'
    ]

    # Extract found keywords
    found_tech = []
    found_verbs = []

    desc_lower = job_description.lower()

    for keyword in common_tech_keywords:
        if keyword.lower() in desc_lower:
            found_tech.append(keyword)

    for verb in action_verbs:
        if verb in desc_lower:
            found_verbs.append(verb)

    # Extract years of experience patterns
    experience_patterns = re.findall(r'(\d+\+?)\s*years?\s*(?:of\s*)?experience', desc_lower, re.IGNORECASE)
    experience = experience_patterns if experience_patterns else []

    fallback_result = f"""
{{
  "MUST_HAVE_KEYWORDS": {{
    "technical_skills": {found_tech[:10]},
    "certifications_and_qualifications": [],
    "years_of_experience": {experience},
    "industry_specific_terms": []
  }},
  "NICE_TO_HAVE_KEYWORDS": {{
    "soft_skills": [],
    "preferred_qualifications": [],
    "domain_knowledge": []
  }},
  "ACTION_VERBS": {found_verbs[:8]},
  "KEYWORD_VARIATIONS": {{
    "note": "This is a fallback extraction due to API unavailability. Results may be less comprehensive."
  }}
}}
"""

    return fallback_result


# Match student CV against job keywords
def keyword_gap_analysis(student_cv, job_keywords, max_retries=None):
    """
    Identify missing keywords and suggest where to add them
    Includes retry logic for handling API overload
    """
    import time
    import random

    # Use configuration values if not specified
    if max_retries is None:
        max_retries = API_CONFIG['max_retries']

    retry_delay_base = API_CONFIG['retry_delay_base']

    for attempt in range(max_retries):
        try:
            if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
                return _gap_analysis_fallback(student_cv, job_keywords)
            response = get_client().models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""
                Compare student CV against required job keywords:

                Student CV: {student_cv}
                Job Keywords: {job_keywords}

                Provide:
                1. Keywords PRESENT in CV (mark with ✅)
                2. Keywords MISSING from CV (mark with ❌)
                3. Suggestions for adding missing keywords:
                   - Which CV section to add them (Summary, Experience, Skills)
                   - How to incorporate naturally (provide reworded bullet points)
                   - Semantic alternatives if exact match impossible

                IMPORTANT: Never fabricate experience. Only suggest adding keywords where:
                - Student has relevant experience but didn't mention keyword
                - Transferable skills apply
                - Academic projects demonstrate the skill

                Return analysis in structured format.
                """
            )

            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            error_message = str(e)
            if ("503" in error_message or "UNAVAILABLE" in error_message or
                "429" in error_message or "RESOURCE_EXHAUSTED" in error_message or
                "QUOTA" in error_message.lower()):
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter using configured base
                    wait_time = (retry_delay_base ** attempt) + random.uniform(0, 1)
                    logger.warning(f"API rate limited/overloaded (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("API still rate limited after all retries. Using fallback gap analysis.")
                    return _gap_analysis_fallback(student_cv, job_keywords)
            else:
                # Non-retryable error, don't retry
                logger.error(f"Error in keyword gap analysis: {e}", exc_info=True)
                return _gap_analysis_fallback(student_cv, job_keywords)

    # This should not be reached, but just in case
    return _gap_analysis_fallback(student_cv, job_keywords)


def _gap_analysis_fallback(student_cv, job_keywords):
    """
    Fallback gap analysis when API is unavailable
    Uses simple text matching for basic keyword presence/absence
    """
    import re
    import json

    try:
        # Parse job keywords if it's JSON
        if isinstance(job_keywords, str) and job_keywords.startswith('{'):
            keywords_data = json.loads(job_keywords.replace('```json', '').replace('```', ''))
        else:
            # If not JSON, treat as plain text
            keywords_data = {"fallback": job_keywords}

        cv_lower = student_cv.lower()

        # Extract all keywords from the job keywords structure
        all_keywords = []
        if "MUST_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["MUST_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "NICE_TO_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["NICE_TO_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "ACTION_VERBS" in keywords_data:
            if isinstance(keywords_data["ACTION_VERBS"], list):
                all_keywords.extend(keywords_data["ACTION_VERBS"])

        # Check presence of keywords
        present_keywords = []
        missing_keywords = []

        for keyword in all_keywords:
            if isinstance(keyword, str) and len(keyword.strip()) > 0:
                if keyword.lower() in cv_lower:
                    present_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

        fallback_result = f"""
**Keyword Gap Analysis (Fallback Mode)**

**Keywords PRESENT in CV:**
{chr(10).join(f"✅ {kw}" for kw in present_keywords[:10])}

**Keywords MISSING from CV:**
{chr(10).join(f"❌ {kw}" for kw in missing_keywords[:10])}

**Basic Suggestions:**
• Add missing technical skills to the Skills section
• Include relevant keywords in project descriptions
• Consider adding keywords to your professional summary

*Note: This is a simplified analysis due to API unavailability. Full AI-powered analysis provides more detailed suggestions.*
"""

        return fallback_result

    except Exception as e:
        return f"Fallback analysis failed: {e}. Raw keywords: {job_keywords[:200]}..."
