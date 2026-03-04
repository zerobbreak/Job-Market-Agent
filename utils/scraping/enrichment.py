"""
AI and pattern-based job enrichment.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_skills_from_description(description: str) -> List[str]:
    """
    Extract technical skills from job description using pattern matching.
    """
    if not description:
        return []

    common_skills = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
        'TypeScript', 'Swift', 'Kotlin', 'Scala', 'R', 'HTML', 'CSS', 'React',
        'Angular', 'Vue', 'Node.js', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB',
        'Redis', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git',
        'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Machine Learning', 'AI',
        'Data Science', 'Pandas', 'NumPy', 'TensorFlow', 'PyTorch', 'Agile', 'Scrum'
    ]

    found_skills = []
    description_lower = description.lower()

    for skill in common_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)

    # Synonyms
    variations = {'js': 'JavaScript', 'py': 'Python', 'ml': 'Machine Learning', 'k8s': 'Kubernetes'}
    for abbr, full in variations.items():
        if f" {abbr} " in f" {description_lower} " and full not in found_skills:
            found_skills.append(full)

    return list(set(found_skills))


def extract_job_keywords(description: str) -> str:
    """
    Extract categorized keywords from job description using pattern matching.
    Returns a JSON string.
    """
    technical = extract_skills_from_description(description)
    
    soft_skills = ['communication', 'leadership', 'teamwork', 'problem solving', 'adaptability']
    found_soft = [s for s in soft_skills if s.lower() in description.lower()]

    action_verbs = ['develop', 'design', 'implement', 'manage', 'analyze', 'lead']
    found_verbs = [v for v in action_verbs if v.lower() in description.lower()]

    # Years of experience pattern
    exp_years = re.findall(r'(\d+\+?)\s*years?', description, re.IGNORECASE)

    result = {
        "MUST_HAVE_KEYWORDS": {
            "technical_skills": technical[:12],
            "years_of_experience": exp_years,
        },
        "NICE_TO_HAVE_KEYWORDS": {
            "soft_skills": found_soft[:6],
        },
        "ACTION_VERBS": found_verbs[:10],
    }
    return json.dumps(result)


def semantic_skill_match(student_skills: List[str], required_skills: List[str]) -> tuple[List[Dict[str, Any]], float]:
    """
    Perform semantic matching between student skills and required skills.
    """
    if not student_skills or not required_skills:
        return [], 0.0

    matches = []
    student_lower = [s.lower() for s in student_skills]
    
    for req in required_skills:
        req_l = req.lower()
        if req_l in student_lower:
            matches.append({
                'required': req,
                'student_has': student_skills[student_lower.index(req_l)],
                'confidence': 1.0
            })
        # Basic synonym/substring check could go here
        
    match_percentage = (len(matches) / len(required_skills) * 100) if required_skills else 0
    return matches, match_percentage


async def enrich_job_with_ai(job: Dict[str, Any], settings: Any = None) -> Dict[str, Any]:
    """
    Placeholder for Gemini-based enrichment.
    """
    job['extracted_skills'] = extract_skills_from_description(job.get('description', ''))
    return job


def keyword_gap_analysis(student_cv: str, job_keywords: Any) -> str:
    """
    Identify missing keywords and suggest where to add them.
    """
    if not student_cv or not job_keywords:
        return "Not enough data for gap analysis."

    cv_lower = student_cv.lower()
    
    # Simple extraction if job_keywords is JSON-like string
    all_keywords = []
    if isinstance(job_keywords, str) and job_keywords.startswith('{'):
        try:
            data = json.loads(job_keywords)
            for cat in data.get("MUST_HAVE_KEYWORDS", {}).values():
                if isinstance(cat, list): all_keywords.extend(cat)
        except:
            pass
    
    present = [k for k in all_keywords if k.lower() in cv_lower]
    missing = [k for k in all_keywords if k.lower() not in cv_lower]

    result = f"**Keywords PRESENT:** {', '.join(present[:10])}\n\n"
    result += f"**Keywords MISSING:** {', '.join(missing[:10])}\n\n"
    result += "**Suggestions:**\n- Add missing technical skills to your Skills section."
    
    return result
