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
            # In OpenRouter-only mode, retrieve all jobs and filter by relevance
            try:
                # Get all jobs from the collection (limit to reasonable number for performance)
                all_results = jobs_collection.get(limit=50, include=['metadatas'])

                # Filter jobs based on basic relevance to student profile
                relevant_jobs = []
                query_keywords = set()
                if student_profile.get('desired_role'):
                    query_keywords.update(student_profile['desired_role'].lower().split())
                if student_profile.get('industry'):
                    query_keywords.update(student_profile['industry'].lower().split())
                if student_profile.get('skills'):
                    query_keywords.update([skill.lower() for skill in student_profile['skills']])

                for job_id, metadata in zip(all_results['ids'], all_results['metadatas']):
                    if metadata:
                        # Check if job title, company, or description contains relevant keywords
                        job_text = (
                            metadata.get('title', '').lower() + ' ' +
                            metadata.get('company', '').lower() + ' ' +
                            metadata.get('description', '').lower()
                        )

                        # Calculate simple relevance score based on keyword matches
                        matches = sum(1 for keyword in query_keywords if keyword in job_text)
                        relevance_score = min(100, matches * 20)  # Scale to 0-100

                        if relevance_score > 20:  # Only include somewhat relevant jobs
                            relevant_jobs.append((job_id, metadata, relevance_score))

                # Sort by relevance and take top matches
                relevant_jobs.sort(key=lambda x: x[2], reverse=True)
                top_jobs = relevant_jobs[:10]

                # Format results to match the expected structure
                results = {
                    'ids': [[job_id for job_id, _, _ in top_jobs]],
                    'metadatas': [[metadata for _, metadata, _ in top_jobs]]
                }

            except Exception as e:
                print(f"OpenRouter-only job retrieval failed: {e}")
                results = {'ids': [[]], 'metadatas': [[]]}
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
