"""
Job matching utilities for comparing student profiles with job opportunities
"""

from .scraping import semantic_skill_match
from .database import jobs_collection
import google.genai as genai
import os

# Lazy-initialize Gemini client for embeddings
client = None


def get_client():
    if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
        raise RuntimeError("OpenRouter-only mode enabled; Google GenAI disabled")
    global client
    if client is None:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        client = genai.Client(api_key=api_key)
    return client


def match_student_to_jobs(student_profile):
    """
    Match a student profile to jobs in the ChromaDB collection
    """
    from agents import job_matcher
    from .scraping import extract_job_keywords, keyword_gap_analysis

    student_skills = student_profile.get('skills', [])
    student_cv_text = student_profile.get('cv_text', '')  # Full CV text for keyword analysis

    try:
        # Create embedding for the student profile summary
        query_text = student_profile.get('summary', '')
        if not query_text:
            query_text = f"{student_profile.get('desired_role', '')} {student_profile.get('industry', '')}"

        if os.getenv('OPENROUTER_ONLY', 'true').lower() == 'true':
            # Basic metadata-only scan in OpenRouter-only mode
            # Note: Without embeddings, perform a naive filter on stored metadatas
            results = {'ids': [[]], 'metadatas': [[]]}
            try:
                # Chroma doesn't provide simple metadata scans in-memory here;
                # rely on stored collection if available via get
                pass
            except Exception:
                pass
        else:
            query_response = get_client().models.embed_content(
                model="text-embedding-004",
                contents=query_text
            )
            query_embedding = query_response.embeddings[0].values

            # Query similar jobs from ChromaDB using manual embeddings
            results = jobs_collection.query(
                query_embeddings=[query_embedding],
                n_results=10
            )

        matched_jobs = []
        for i, job_id in enumerate(results['ids'][0]):
            job_metadata = results['metadatas'][0][i]
            # Convert skills string back to list
            skills_str = job_metadata.get('required_skills', '')
            required_skills = [s.strip() for s in skills_str.split(',')] if skills_str else []

            # Perform semantic skill matching
            skill_matches, match_score = semantic_skill_match(student_skills, required_skills)

            # Extract job keywords using AI
            job_description = job_metadata.get('description', '')
            if job_description:
                job_keywords = extract_job_keywords(job_description)

                # Perform keyword gap analysis if we have CV text
                gap_analysis = ""
                if student_cv_text:
                    gap_analysis = keyword_gap_analysis(student_cv_text, job_keywords)
            else:
                job_keywords = "No job description available"
                gap_analysis = "No job description available for keyword analysis"

            # Use the agent to perform detailed analysis
            analysis = job_matcher.run(f"""
            Analyze this job match:

            Student Profile: {student_profile}
            Job Description: {job_metadata.get('description', '')}
            Company: {job_metadata.get('company', '')}
            Required Skills: {required_skills}
            Skill Match Score: {match_score:.1f}%
            Skill Matches: {skill_matches}

            Job Keywords: {job_keywords}
            Keyword Gap Analysis: {gap_analysis}

            Provide a comprehensive match analysis with scores, including keyword optimization suggestions.
            """)

            matched_jobs.append({
                'job_id': job_id,
                'match_score': match_score,
                'analysis': analysis.content,
                'job_keywords': job_keywords,
                'keyword_gaps': gap_analysis
            })

        return matched_jobs

    except Exception as e:
        print(f"Error matching jobs: {e}")
        return []
