"""
Job matching utilities for comparing student profiles with job opportunities
"""

from .scraping import semantic_skill_match
from .database import job_db
from .scraping import extract_skills_from_description

def match_student_to_jobs(student_profile):
    """
    Match a student profile to jobs using TF-IDF similarity and skill matching
    """
    from .scraping import extract_job_keywords, keyword_gap_analysis

    student_skills = student_profile.get('skills', [])
    student_cv_text = student_profile.get('cv_text', '')  # Full CV text for keyword analysis

    try:
        # Create search query from student profile
        desired_role = student_profile.get('desired_role', '')
        industry = student_profile.get('industry', '')
        skills_text = ' '.join(student_skills)

        # Build search query
        query_parts = []
        if desired_role:
            query_parts.append(desired_role)
        if industry:
            query_parts.append(industry)
        if skills_text:
            query_parts.append(skills_text)

        search_query = ' '.join(query_parts)

        # Search jobs using full-text search
        search_results = job_db.search_jobs(search_query, limit=20)

        matched_jobs = []
        for job in search_results:
            # Get job skills
            required_skills = job.get('skills', [])
            if not required_skills:
                # Extract skills from description if not already extracted
                job_desc = job.get('description', '')
                required_skills = extract_skills_from_description(job_desc)
                job['skills'] = required_skills

            # Perform semantic skill matching
            skill_matches, match_score = semantic_skill_match(student_skills, required_skills)

            # Extract job keywords using AI
            job_description = job.get('description', '')
            if job_description:
                job_keywords = extract_job_keywords(job_description)

                # Perform keyword gap analysis if we have CV text
                gap_analysis = ""
                if student_cv_text:
                    gap_analysis = keyword_gap_analysis(student_cv_text, job_keywords)
            else:
                job_keywords = "No job description available"
                gap_analysis = "No job description available for keyword analysis"

            # Create analysis without AI agent (simplified)
            analysis = f"""
Job Match Analysis for {job.get('title', 'Unknown Position')} at {job.get('company', 'Unknown Company')}

Skill Match: {match_score:.1f}%
Matched Skills: {', '.join([m['student_has'] for m in skill_matches[:5]]) if skill_matches else 'None'}

Job Requirements: {', '.join(required_skills[:10]) if required_skills else 'Not specified'}

Recommendations:
- Focus on highlighting your experience with: {', '.join([m['required'] for m in skill_matches[:3]]) if skill_matches else 'relevant technologies'}
- Consider adding keywords: {', '.join(required_skills[:5]) if required_skills else 'from job description'}
            """

            matched_jobs.append({
                'job_id': job['id'],
                'job_title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'match_score': match_score,
                'skill_matches': skill_matches,
                'required_skills': required_skills,
                'job_url': job['url'],
                'analysis': analysis,
                'job_keywords': job_keywords,
                'keyword_gaps': gap_analysis,
                'relevance_score': job.get('relevance_score', 0.0)
            })

        return matched_jobs

    except Exception as e:
        print(f"Error matching jobs: {e}")
        return []
