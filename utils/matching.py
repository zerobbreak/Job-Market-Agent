"""
Job matching utilities for comparing student profiles with job opportunities
"""

from .scraping import semantic_skill_match
from .database import jobs_collection
import google.genai as genai
import os

# Initialize Gemini client for embeddings
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


def match_student_to_jobs(student_profile):
    """
    Match a student profile to jobs in the ChromaDB collection
    """
    from agents import job_matcher

    student_skills = student_profile.get('skills', [])

    try:
        # Create embedding for the student profile summary
        query_text = student_profile.get('summary', '')
        if not query_text:
            query_text = f"{student_profile.get('desired_role', '')} {student_profile.get('industry', '')}"

        query_response = client.models.embed_content(
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

            # Use the agent to perform detailed analysis
            analysis = job_matcher.run(f"""
            Analyze this job match:

            Student Profile: {student_profile}
            Job Description: {job_metadata.get('description', '')}
            Company: {job_metadata.get('company', '')}
            Required Skills: {required_skills}
            Skill Match Score: {match_score:.1f}%
            Skill Matches: {skill_matches}

            Provide a comprehensive match analysis with scores.
            """)

            matched_jobs.append({
                'job_id': job_id,
                'match_score': match_score,
                'analysis': analysis.content
            })

        return matched_jobs

    except Exception as e:
        print(f"Error matching jobs: {e}")
        return []
